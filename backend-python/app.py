"""
SIEM Platform - Main Flask Application
Provides REST API and WebSocket endpoints for security event management.
"""

import os
import logging
import traceback
from datetime import datetime, timezone
from functools import wraps

import jwt
import psycopg2
import psycopg2.extras
from bson import ObjectId
from dotenv import load_dotenv
from flask import Flask, jsonify, request, g
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

from modules.log_parser import LogParser
from modules.correlation_engine import CorrelationEngine
from modules.threat_intel import ThreatIntel
from modules.incident_response import IncidentResponse

load_dotenv()

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")
app.config["JWT_ALGORITHM"] = os.environ.get("JWT_ALGORITHM", "HS256")

CORS(app, resources={r"/api/*": {"origins": os.environ.get("ALLOWED_ORIGINS", "*")}})
socketio = SocketIO(
    app,
    cors_allowed_origins=os.environ.get("ALLOWED_ORIGINS", "*"),
    async_mode="eventlet",
    logger=False,
    engineio_logger=False,
)

# ---------------------------------------------------------------------------
# Module singletons
# ---------------------------------------------------------------------------
log_parser = LogParser()
correlation_engine = CorrelationEngine()
threat_intel = ThreatIntel()
incident_response = IncidentResponse()


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------
def get_postgres():
    """Return a cached PostgreSQL connection for this request context."""
    if "pg_conn" not in g:
        try:
            g.pg_conn = psycopg2.connect(
                host=os.environ.get("POSTGRES_HOST", "localhost"),
                port=int(os.environ.get("POSTGRES_PORT", 5432)),
                dbname=os.environ.get("POSTGRES_DB", "siem"),
                user=os.environ.get("POSTGRES_USER", "siem_user"),
                password=os.environ.get("POSTGRES_PASSWORD", ""),
                cursor_factory=psycopg2.extras.RealDictCursor,
                connect_timeout=5,
            )
        except psycopg2.OperationalError as exc:
            logger.warning("PostgreSQL unavailable: %s", exc)
            g.pg_conn = None
    return g.pg_conn


def get_mongo():
    """Return a cached MongoDB database handle for this request context."""
    if "mongo_db" not in g:
        try:
            client = MongoClient(
                os.environ.get("MONGO_URI", "mongodb://localhost:27017"),
                serverSelectionTimeoutMS=3000,
            )
            client.admin.command("ping")
            g.mongo_db = client[os.environ.get("MONGO_DB", "siem")]
        except ConnectionFailure as exc:
            logger.warning("MongoDB unavailable: %s", exc)
            g.mongo_db = None
    return g.mongo_db


@app.teardown_appcontext
def close_connections(_exc):
    pg_conn = g.pop("pg_conn", None)
    if pg_conn is not None:
        try:
            pg_conn.close()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# JWT authentication
# ---------------------------------------------------------------------------
def require_auth(f):
    """Decorator that validates JWT bearer token and populates g.current_user."""

    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid Authorization header"}), 401
        token = auth_header.split(" ", 1)[1]
        try:
            payload = jwt.decode(
                token,
                app.config["SECRET_KEY"],
                algorithms=[app.config["JWT_ALGORITHM"]],
            )
            g.current_user = payload
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError as exc:
            return jsonify({"error": f"Invalid token: {exc}"}), 401
        return f(*args, **kwargs)

    return decorated


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.route("/health", methods=["GET"])
def health():
    """Service health check endpoint."""
    pg_ok = get_postgres() is not None
    mongo_ok = get_mongo() is not None
    status = "healthy" if (pg_ok or mongo_ok) else "degraded"
    return jsonify(
        {
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "services": {
                "postgres": "connected" if pg_ok else "unavailable",
                "mongodb": "connected" if mongo_ok else "unavailable",
            },
        }
    ), 200


# ---------------------------------------------------------------------------
# Log ingestion
# ---------------------------------------------------------------------------
@app.route("/api/logs/ingest", methods=["POST"])
@require_auth
def ingest_logs():
    """
    Ingest raw log data, parse, normalise, correlate, and store.

    Accepts JSON body:
        {
            "raw_log": "<log string>",
            "format": "auto|syslog|json|cef|leef",   (optional)
            "source": "<source identifier>"           (optional)
        }
    """
    body = request.get_json(silent=True) or {}
    raw_log = body.get("raw_log", "")
    fmt = body.get("format", "auto")
    source = body.get("source", "unknown")

    if not raw_log:
        return jsonify({"error": "raw_log field is required"}), 400

    try:
        parsed = log_parser.parse(raw_log, format=fmt)
        normalized = log_parser.normalize(parsed)
        normalized["source"] = source
        normalized["ingested_at"] = datetime.now(timezone.utc).isoformat()

        # Persist to MongoDB when available
        db = get_mongo()
        inserted_id = None
        if db is not None:
            result = db.logs.insert_one(normalized.copy())
            inserted_id = str(result.inserted_id)

        # Feed event into the correlation engine
        correlation_engine.add_event(normalized)
        new_alerts = correlation_engine.correlate()

        if new_alerts:
            _store_alerts(new_alerts)
            socketio.emit("new_alerts", {"alerts": new_alerts}, room="alerts")

        return jsonify(
            {
                "status": "ingested",
                "log_id": inserted_id,
                "parsed": normalized,
                "alerts_generated": len(new_alerts),
            }
        ), 201

    except Exception as exc:
        logger.error("Log ingestion error: %s\n%s", exc, traceback.format_exc())
        return jsonify({"error": "Internal server error during log ingestion"}), 500


def _store_alerts(alerts: list):
    """Persist a list of alert dicts to MongoDB."""
    db = get_mongo()
    if db is None:
        return
    for alert in alerts:
        alert.setdefault("status", "open")
        alert.setdefault("created_at", datetime.now(timezone.utc).isoformat())
    db.alerts.insert_many([a.copy() for a in alerts])


# ---------------------------------------------------------------------------
# Alerts
# ---------------------------------------------------------------------------
@app.route("/api/alerts", methods=["GET"])
@require_auth
def get_alerts():
    """
    Retrieve alerts with optional filtering.

    Query params: status, severity, limit, offset
    """
    status_filter = request.args.get("status")
    severity_filter = request.args.get("severity")
    limit = min(int(request.args.get("limit", 50)), 500)
    offset = int(request.args.get("offset", 0))

    query: dict = {}
    if status_filter:
        query["status"] = status_filter
    if severity_filter:
        query["severity"] = severity_filter

    db = get_mongo()
    if db is None:
        # Return in-memory alerts from the correlation engine as a fallback
        alerts = correlation_engine.get_recent_alerts()
        return jsonify({"alerts": alerts, "total": len(alerts), "source": "in-memory"})

    try:
        cursor = db.alerts.find(query).sort("created_at", -1).skip(offset).limit(limit)
        alerts = []
        for doc in cursor:
            doc["_id"] = str(doc["_id"])
            alerts.append(doc)
        total = db.alerts.count_documents(query)
        return jsonify({"alerts": alerts, "total": total, "limit": limit, "offset": offset})
    except Exception as exc:
        logger.error("Alert retrieval error: %s", exc)
        return jsonify({"error": "Failed to retrieve alerts"}), 500


@app.route("/api/alerts/<alert_id>/respond", methods=["POST"])
@require_auth
def respond_to_alert(alert_id: str):
    """
    Trigger an automated or manual response to an alert.

    Body:
        {
            "action": "acknowledge|escalate|resolve|execute_playbook",
            "playbook": "<playbook_name>",  (required when action == execute_playbook)
            "notes": "<analyst notes>"      (optional)
        }
    """
    body = request.get_json(silent=True) or {}
    action = body.get("action")
    if not action:
        return jsonify({"error": "action field is required"}), 400

    db = get_mongo()
    alert = None
    if db is not None:
        try:
            doc = db.alerts.find_one({"_id": ObjectId(alert_id)})
            if doc:
                doc["_id"] = str(doc["_id"])
                alert = doc
        except Exception:
            pass

    if alert is None:
        # Fallback: create a minimal context dict so playbooks can still run
        alert = {"_id": alert_id, "status": "unknown"}

    result = {"alert_id": alert_id, "action": action}

    try:
        if action == "acknowledge":
            _update_alert_status(db, alert_id, "acknowledged", body.get("notes"))
            result["status"] = "acknowledged"
        elif action == "resolve":
            _update_alert_status(db, alert_id, "resolved", body.get("notes"))
            result["status"] = "resolved"
        elif action == "escalate":
            _update_alert_status(db, alert_id, "escalated", body.get("notes"))
            result["status"] = "escalated"
        elif action == "execute_playbook":
            playbook_name = body.get("playbook")
            if not playbook_name:
                return jsonify({"error": "playbook field is required"}), 400
            pb_result = incident_response.execute_playbook(playbook_name, alert)
            result["playbook_result"] = pb_result
            _update_alert_status(db, alert_id, "in_remediation", body.get("notes"))
        else:
            return jsonify({"error": f"Unknown action: {action}"}), 400

        socketio.emit("alert_updated", result, room="alerts")
        return jsonify(result)

    except Exception as exc:
        logger.error("Alert response error: %s\n%s", exc, traceback.format_exc())
        return jsonify({"error": "Internal server error during alert response"}), 500


def _update_alert_status(db, alert_id: str, status: str, notes: str | None):
    if db is None:
        return
    update = {
        "$set": {
            "status": status,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
    }
    if notes:
        update["$push"] = {"notes": {"text": notes, "ts": datetime.now(timezone.utc).isoformat()}}
    try:
        db.alerts.update_one({"_id": ObjectId(alert_id)}, update)
    except Exception as exc:
        logger.warning("Could not update alert %s: %s", alert_id, exc)


# ---------------------------------------------------------------------------
# Threat intelligence
# ---------------------------------------------------------------------------
@app.route("/api/threat-intel", methods=["GET"])
@require_auth
def get_threat_intel():
    """
    Query threat intelligence feeds.

    Query params: ip, domain, hash, cve
    """
    ip = request.args.get("ip")
    domain = request.args.get("domain")
    file_hash = request.args.get("hash")
    cve_id = request.args.get("cve")

    if not any([ip, domain, file_hash, cve_id]):
        feeds = threat_intel.get_all_feeds()
        return jsonify({"feeds": feeds})

    results: dict = {}
    try:
        if ip:
            results["ip"] = threat_intel.check_ip(ip)
        if domain:
            results["domain"] = threat_intel.check_domain(domain)
        if file_hash:
            results["hash"] = threat_intel.check_hash(file_hash)
        if cve_id:
            results["cve"] = threat_intel.check_cve(cve_id)

        indicators = [v for v in results.values() if v]
        results["risk_score"] = threat_intel.calculate_risk_score(indicators)
        return jsonify(results)

    except Exception as exc:
        logger.error("Threat intel query error: %s", exc)
        return jsonify({"error": "Failed to retrieve threat intelligence"}), 500


# ---------------------------------------------------------------------------
# Playbooks
# ---------------------------------------------------------------------------
@app.route("/api/playbooks/execute", methods=["POST"])
@require_auth
def execute_playbook():
    """
    Manually execute a response playbook.

    Body:
        {
            "playbook": "<playbook_name>",
            "context": { ... }
        }
    """
    body = request.get_json(silent=True) or {}
    playbook_name = body.get("playbook")
    context = body.get("context", {})

    if not playbook_name:
        return jsonify({"error": "playbook field is required"}), 400

    try:
        result = incident_response.execute_playbook(playbook_name, context)
        incident_response.audit_log(
            action=f"manual_playbook:{playbook_name}",
            context={**context, "executed_by": g.current_user.get("sub", "unknown")},
        )
        return jsonify({"playbook": playbook_name, "result": result})
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        logger.error("Playbook execution error: %s\n%s", exc, traceback.format_exc())
        return jsonify({"error": "Internal server error during playbook execution"}), 500


# ---------------------------------------------------------------------------
# WebSocket events
# ---------------------------------------------------------------------------
@socketio.on("connect")
def on_connect():
    logger.info("WebSocket client connected: %s", request.sid)
    emit("connected", {"message": "Connected to SIEM real-time feed"})


@socketio.on("disconnect")
def on_disconnect():
    logger.info("WebSocket client disconnected: %s", request.sid)


@socketio.on("subscribe")
def on_subscribe(data: dict):
    """Allow clients to subscribe to named rooms (e.g. 'alerts', 'logs')."""
    room = data.get("room", "alerts")
    join_room(room)
    emit("subscribed", {"room": room})


# ---------------------------------------------------------------------------
# Generic error handlers
# ---------------------------------------------------------------------------
@app.errorhandler(404)
def not_found(_e):
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(405)
def method_not_allowed(_e):
    return jsonify({"error": "Method not allowed"}), 405


@app.errorhandler(500)
def internal_error(_e):
    return jsonify({"error": "Internal server error"}), 500


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    logger.info("Starting SIEM backend on port %d (debug=%s)", port, debug)
    socketio.run(app, host="0.0.0.0", port=port, debug=debug)
