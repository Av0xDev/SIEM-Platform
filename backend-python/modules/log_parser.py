"""
Log Parser Module
Parses raw log data in multiple formats (syslog, JSON, CEF, LEEF) and
normalises events to a common schema for downstream correlation.
"""

import json
import logging
import re
from datetime import datetime, timezone
from typing import Any

from dateutil import parser as dateutil_parser

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Regex patterns for common log formats
# ---------------------------------------------------------------------------
_SYSLOG_RE = re.compile(
    r"^(?P<priority><\d+>)?"
    r"(?P<timestamp>\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})"
    r"\s+(?P<hostname>\S+)"
    r"\s+(?P<process>[^\[:\s]+)(?:\[(?P<pid>\d+)\])?"
    r":\s+(?P<message>.*)$",
    re.DOTALL,
)
_RFC5424_RE = re.compile(
    r"^(?P<priority><\d+>)"
    r"(?P<version>\d)\s+"
    r"(?P<timestamp>\S+)\s+"
    r"(?P<hostname>\S+)\s+"
    r"(?P<app>\S+)\s+"
    r"(?P<procid>\S+)\s+"
    r"(?P<msgid>\S+)\s+"
    r"(?P<structured_data>\[.*?\]|-)\s*"
    r"(?P<message>.*)$",
    re.DOTALL,
)
_CEF_RE = re.compile(
    r"^(?:(?P<syslog_header>.*?)\s+)?"
    r"CEF:(?P<version>\d+)"
    r"\|(?P<device_vendor>[^|]*)"
    r"\|(?P<device_product>[^|]*)"
    r"\|(?P<device_version>[^|]*)"
    r"\|(?P<signature_id>[^|]*)"
    r"\|(?P<name>[^|]*)"
    r"\|(?P<severity>[^|]*)"
    r"\|(?P<extensions>.*)$",
    re.DOTALL,
)
_LEEF_RE = re.compile(
    r"^LEEF:(?P<version>[\d.]+)"
    r"\|(?P<vendor>[^|]*)"
    r"\|(?P<product>[^|]*)"
    r"\|(?P<product_version>[^|]*)"
    r"\|(?P<event_id>[^|]*)"
    r"\|(?P<attributes>.*)$",
    re.DOTALL,
)
_IP_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
_SEVERITY_WORDS = {
    "emergency": "critical",
    "emerg": "critical",
    "alert": "high",
    "critical": "critical",
    "crit": "critical",
    "error": "high",
    "err": "high",
    "warning": "medium",
    "warn": "medium",
    "notice": "low",
    "informational": "info",
    "info": "info",
    "debug": "debug",
}

# Syslog priority → severity string
_PRIORITY_SEVERITY = {
    0: "critical",
    1: "critical",
    2: "critical",
    3: "high",
    4: "medium",
    5: "low",
    6: "info",
    7: "debug",
}


class LogParser:
    """
    Parse raw log strings in multiple formats and normalise to a common schema.

    Supported formats: syslog (RFC 3164 & 5424), JSON, CEF, LEEF.
    When format='auto', the parser attempts each format in turn.
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def parse(self, raw_log: str, format: str = "auto") -> dict[str, Any]:
        """
        Parse *raw_log* using the specified *format*.

        Parameters
        ----------
        raw_log:
            The raw log string.
        format:
            One of ``'auto'``, ``'syslog'``, ``'json'``, ``'cef'``, ``'leef'``.

        Returns
        -------
        dict
            Parsed log fields.  Always contains at least ``raw`` and
            ``format`` keys.

        Raises
        ------
        ValueError
            If *format* is not recognised.
        """
        raw_log = raw_log.strip()
        dispatch = {
            "syslog": self.parse_syslog,
            "json": self.parse_json,
            "cef": self.parse_cef,
            "leef": self.parse_leef,
        }

        if format != "auto":
            if format not in dispatch:
                raise ValueError(f"Unknown log format: {format!r}")
            result = dispatch[format](raw_log)
            result["raw"] = raw_log
            return result

        # Auto-detection order: CEF > LEEF > JSON > syslog RFC5424 > syslog RFC3164
        for fmt_name, parser_fn in dispatch.items():
            try:
                result = parser_fn(raw_log)
                if result.get("_parsed"):
                    result["raw"] = raw_log
                    result.pop("_parsed", None)
                    return result
            except Exception:
                continue

        # Fallback: treat the entire string as an unstructured message
        logger.debug("Could not parse log, returning raw: %.80s…", raw_log)
        return {"raw": raw_log, "format": "unknown", "message": raw_log}

    def parse_syslog(self, raw_log: str) -> dict[str, Any]:
        """
        Parse a syslog message (RFC 3164 or RFC 5424).

        Returns an empty ``_parsed=False`` dict when the input does not
        match the expected format.
        """
        for pattern, fmt_name in [(_RFC5424_RE, "syslog_rfc5424"), (_SYSLOG_RE, "syslog_rfc3164")]:
            m = pattern.match(raw_log)
            if m:
                data = m.groupdict()
                data["format"] = fmt_name
                data["_parsed"] = True
                # Decode priority → facility + severity
                if data.get("priority"):
                    pri = int(data["priority"].strip("<>"))
                    data["facility"] = pri >> 3
                    data["severity"] = _PRIORITY_SEVERITY.get(pri & 0x07, "info")
                return data
        return {"_parsed": False, "format": "syslog"}

    def parse_json(self, raw_log: str) -> dict[str, Any]:
        """
        Parse a JSON-encoded log message.

        Raises ``ValueError`` when the input is not valid JSON.
        """
        try:
            data = json.loads(raw_log)
            if not isinstance(data, dict):
                return {"_parsed": False, "format": "json"}
            data["format"] = "json"
            data["_parsed"] = True
            return data
        except json.JSONDecodeError:
            return {"_parsed": False, "format": "json"}

    def parse_cef(self, raw_log: str) -> dict[str, Any]:
        """
        Parse an ArcSight Common Event Format (CEF) log line.
        """
        m = _CEF_RE.match(raw_log)
        if not m:
            return {"_parsed": False, "format": "cef"}

        data = m.groupdict()
        data["format"] = "cef"
        data["_parsed"] = True

        # Parse key=value extension pairs, supporting quoted values
        extensions: dict[str, str] = {}
        ext_str = data.pop("extensions", "") or ""
        for kv in re.finditer(r'(\w+)=((?:[^\\=\s]|\\.)*)', ext_str):
            extensions[kv.group(1)] = kv.group(2)
        data["extensions"] = extensions

        # Normalise severity (CEF uses 0-10 integer scale)
        sev_raw = data.get("severity", "")
        try:
            sev_int = int(sev_raw)
            if sev_int <= 3:
                data["severity"] = "low"
            elif sev_int <= 6:
                data["severity"] = "medium"
            elif sev_int <= 8:
                data["severity"] = "high"
            else:
                data["severity"] = "critical"
        except (ValueError, TypeError):
            data["severity"] = _SEVERITY_WORDS.get(sev_raw.lower(), "info")

        return data

    def parse_leef(self, raw_log: str) -> dict[str, Any]:
        """
        Parse an IBM QRadar Log Event Extended Format (LEEF) log line.
        """
        m = _LEEF_RE.match(raw_log)
        if not m:
            return {"_parsed": False, "format": "leef"}

        data = m.groupdict()
        data["format"] = "leef"
        data["_parsed"] = True

        # LEEF 2.0 may use a custom delimiter; fall back to tab
        attr_str = data.pop("attributes", "") or ""
        delimiter = "\t"
        if data.get("version", "1.0").startswith("2") and attr_str.startswith("|"):
            # LEEF 2.0: first pipe-delimited field is the delimiter character
            parts = attr_str[1:].split("|", 1)
            if parts:
                delimiter = parts[0] or "\t"
                attr_str = parts[1] if len(parts) > 1 else ""

        attributes: dict[str, str] = {}
        for pair in attr_str.split(delimiter):
            if "=" in pair:
                k, _, v = pair.partition("=")
                attributes[k.strip()] = v.strip()
        data["attributes"] = attributes

        # Map LEEF severity to common schema
        sev_raw = attributes.get("sev", attributes.get("severity", "")).lower()
        data["severity"] = _SEVERITY_WORDS.get(sev_raw, "info")
        return data

    def normalize(self, parsed_log: dict[str, Any]) -> dict[str, Any]:
        """
        Normalise a parsed log dict to the common SIEM event schema.

        The common schema includes:
            timestamp, hostname, source_ip, dest_ip, user, process,
            message, severity, event_type, format, raw, extra
        """
        schema: dict[str, Any] = {
            "timestamp": None,
            "hostname": None,
            "source_ip": None,
            "dest_ip": None,
            "user": None,
            "process": None,
            "message": None,
            "severity": "info",
            "event_type": "generic",
            "format": parsed_log.get("format", "unknown"),
            "raw": parsed_log.get("raw", ""),
            "extra": {},
        }

        fmt = parsed_log.get("format", "")

        if fmt in ("syslog_rfc3164", "syslog_rfc5424"):
            schema["timestamp"] = self._parse_ts(parsed_log.get("timestamp"))
            schema["hostname"] = parsed_log.get("hostname")
            schema["process"] = parsed_log.get("process") or parsed_log.get("app")
            schema["message"] = parsed_log.get("message")
            schema["severity"] = parsed_log.get("severity", "info")

        elif fmt == "json":
            schema["timestamp"] = self._parse_ts(
                parsed_log.get("timestamp") or parsed_log.get("time") or parsed_log.get("@timestamp")
            )
            schema["hostname"] = parsed_log.get("hostname") or parsed_log.get("host")
            schema["source_ip"] = parsed_log.get("src_ip") or parsed_log.get("source_ip")
            schema["dest_ip"] = parsed_log.get("dest_ip") or parsed_log.get("dst_ip")
            schema["user"] = parsed_log.get("user") or parsed_log.get("username")
            schema["process"] = parsed_log.get("process")
            schema["message"] = parsed_log.get("message") or parsed_log.get("msg")
            schema["severity"] = _SEVERITY_WORDS.get(
                str(parsed_log.get("severity", "info")).lower(), "info"
            )

        elif fmt == "cef":
            ext = parsed_log.get("extensions", {})
            schema["timestamp"] = self._parse_ts(ext.get("rt") or ext.get("deviceReceiptTime"))
            schema["hostname"] = parsed_log.get("device_vendor")
            schema["source_ip"] = ext.get("src")
            schema["dest_ip"] = ext.get("dst")
            schema["user"] = ext.get("suser") or ext.get("duser")
            schema["message"] = parsed_log.get("name")
            schema["severity"] = parsed_log.get("severity", "info")
            schema["event_type"] = parsed_log.get("signature_id", "cef_event")

        elif fmt == "leef":
            attrs = parsed_log.get("attributes", {})
            schema["timestamp"] = self._parse_ts(attrs.get("devTime"))
            schema["hostname"] = attrs.get("src") or parsed_log.get("vendor")
            schema["source_ip"] = attrs.get("src")
            schema["dest_ip"] = attrs.get("dst")
            schema["user"] = attrs.get("usrName")
            schema["message"] = parsed_log.get("event_id")
            schema["severity"] = parsed_log.get("severity", "info")

        else:
            schema["message"] = parsed_log.get("message") or parsed_log.get("raw", "")

        # Fallback timestamp
        if schema["timestamp"] is None:
            schema["timestamp"] = datetime.now(timezone.utc).isoformat()

        # Carry forward any unrecognised keys as extra context
        known = {
            "timestamp", "hostname", "source_ip", "dest_ip", "user",
            "process", "message", "severity", "event_type", "format", "raw",
            "extra", "_parsed", "priority", "facility",
        }
        schema["extra"] = {k: v for k, v in parsed_log.items() if k not in known}
        return schema

    def extract_fields(self, log: dict[str, Any]) -> dict[str, Any]:
        """
        Extract well-known security-relevant fields from a normalised log.

        Returns a dict containing: ips, hostname, user, timestamp, severity.
        """
        raw_text = log.get("raw", "") + " " + (log.get("message") or "")
        ips = list(set(_IP_RE.findall(raw_text)))
        return {
            "ips": ips,
            "source_ip": log.get("source_ip") or (ips[0] if ips else None),
            "dest_ip": log.get("dest_ip") or (ips[1] if len(ips) > 1 else None),
            "hostname": log.get("hostname"),
            "user": log.get("user"),
            "timestamp": log.get("timestamp"),
            "severity": log.get("severity", "info"),
            "process": log.get("process"),
        }

    def enrich(self, log: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        """
        Merge additional *context* into *log*, adding an ``enriched_at`` timestamp.

        Parameters
        ----------
        log:
            A normalised log dict (typically the output of :meth:`normalize`).
        context:
            Arbitrary key/value pairs to merge in.

        Returns
        -------
        dict
            A new dict that is the union of *log* and *context*.
        """
        enriched = {**log, **context}
        enriched["enriched_at"] = datetime.now(timezone.utc).isoformat()
        return enriched

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_ts(raw: Any) -> str | None:
        """
        Convert *raw* (string, int epoch, or None) to an ISO-8601 UTC string.
        Returns ``None`` when the input cannot be parsed.
        """
        if raw is None:
            return None
        if isinstance(raw, (int, float)):
            # Treat large integers as millisecond epoch timestamps
            if raw > 1e10:
                raw = raw / 1000.0
            return datetime.fromtimestamp(raw, tz=timezone.utc).isoformat()
        try:
            dt = dateutil_parser.parse(str(raw))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.isoformat()
        except (ValueError, OverflowError):
            return None
