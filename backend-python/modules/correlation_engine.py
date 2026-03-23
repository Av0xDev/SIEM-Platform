"""
Correlation Engine Module
Groups, correlates, and pattern-matches security events to produce alerts.
"""

import logging
import math
import statistics
import threading
import uuid
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Built-in rule definitions
# ---------------------------------------------------------------------------
_BUILTIN_RULES: list[dict[str, Any]] = [
    {
        "id": "brute_force",
        "name": "Brute Force Authentication Attempt",
        "description": "Multiple failed login attempts from the same source IP within a short time window.",
        "event_filter": {"message_keywords": ["failed", "invalid", "authentication failure", "login failed"]},
        "threshold": 5,
        "window_seconds": 300,
        "group_by": "source_ip",
        "severity": "high",
        "tactic": "Credential Access",
        "technique": "T1110",
    },
    {
        "id": "port_scan",
        "name": "Port Scan Detected",
        "description": "Single source IP connecting to many distinct destination ports in a short window.",
        "event_filter": {"message_keywords": ["connection refused", "port", "syn", "connect"]},
        "threshold": 20,
        "window_seconds": 60,
        "group_by": "source_ip",
        "count_distinct": "dest_port",
        "severity": "medium",
        "tactic": "Discovery",
        "technique": "T1046",
    },
    {
        "id": "data_exfiltration",
        "name": "Potential Data Exfiltration",
        "description": "Unusually large outbound data transfer detected.",
        "event_filter": {"message_keywords": ["bytes_out", "transferred", "upload", "outbound"]},
        "threshold": 3,
        "window_seconds": 3600,
        "group_by": "source_ip",
        "anomaly": "bytes_out",
        "severity": "critical",
        "tactic": "Exfiltration",
        "technique": "T1041",
    },
    {
        "id": "privilege_escalation",
        "name": "Privilege Escalation Attempt",
        "description": "User attempting to escalate privileges.",
        "event_filter": {"message_keywords": ["sudo", "su ", "privilege", "root", "administrator", "runas"]},
        "threshold": 3,
        "window_seconds": 600,
        "group_by": "user",
        "severity": "high",
        "tactic": "Privilege Escalation",
        "technique": "T1548",
    },
    {
        "id": "lateral_movement",
        "name": "Lateral Movement Detected",
        "description": "Sequential access to multiple hosts from the same source.",
        "event_filter": {"message_keywords": ["ssh", "rdp", "smb", "wmi", "psexec", "winrm"]},
        "threshold": 4,
        "window_seconds": 1800,
        "group_by": "source_ip",
        "count_distinct": "hostname",
        "severity": "high",
        "tactic": "Lateral Movement",
        "technique": "T1021",
    },
]


class CorrelationEngine:
    """
    Sliding-window event correlation engine.

    Events are held in an in-memory deque bounded by ``max_events``.
    The :meth:`correlate` method evaluates all built-in rules and returns
    any new alerts.  Alert deduplication prevents the same rule from firing
    twice within its own time window.
    """

    def __init__(
        self,
        max_events: int = 100_000,
        dedup_window_seconds: int = 300,
    ):
        self._events: deque[dict[str, Any]] = deque(maxlen=max_events)
        self._recent_alerts: deque[dict[str, Any]] = deque(maxlen=10_000)
        # {rule_id: {group_value: last_alert_ts}}
        self._dedup_index: dict[str, dict[str, datetime]] = defaultdict(dict)
        self._dedup_window = timedelta(seconds=dedup_window_seconds)
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_event(self, event: dict[str, Any]) -> None:
        """
        Add a normalised event to the correlation window.

        Parameters
        ----------
        event:
            A normalised log dict (output of ``LogParser.normalize``).
        """
        event.setdefault("_corr_ts", datetime.now(timezone.utc))
        with self._lock:
            self._events.append(event)

    def correlate(self) -> list[dict[str, Any]]:
        """
        Evaluate all built-in correlation rules against the current event window.

        Returns
        -------
        list
            Newly generated alert dicts (may be empty).
        """
        new_alerts: list[dict[str, Any]] = []
        with self._lock:
            events_snapshot = list(self._events)

        for rule in _BUILTIN_RULES:
            alerts = self._evaluate_rule(rule, events_snapshot)
            new_alerts.extend(alerts)

        with self._lock:
            self._recent_alerts.extend(new_alerts)
        return new_alerts

    def get_recent_alerts(self) -> list[dict[str, Any]]:
        """Return a snapshot of recently generated alerts (newest first)."""
        with self._lock:
            alerts = list(self._recent_alerts)
        alerts.reverse()
        return alerts

    def generate_alert(self, events: list[dict[str, Any]], rule: dict[str, Any]) -> dict[str, Any]:
        """
        Build an alert dict from a list of correlated *events* and the matching *rule*.

        Parameters
        ----------
        events:
            The events that triggered the rule.
        rule:
            The correlation rule dict.

        Returns
        -------
        dict
            A fully populated alert dict.
        """
        source_ips = list({e.get("source_ip") for e in events if e.get("source_ip")})
        users = list({e.get("user") for e in events if e.get("user")})
        hostnames = list({e.get("hostname") for e in events if e.get("hostname")})

        return {
            "alert_id": str(uuid.uuid4()),
            "rule_id": rule["id"],
            "rule_name": rule["name"],
            "description": rule["description"],
            "severity": rule.get("severity", "medium"),
            "tactic": rule.get("tactic"),
            "technique": rule.get("technique"),
            "event_count": len(events),
            "source_ips": source_ips,
            "users": users,
            "hostnames": hostnames,
            "first_seen": self._ts_str(min(e.get("_corr_ts", datetime.now(timezone.utc)) for e in events)),
            "last_seen": self._ts_str(max(e.get("_corr_ts", datetime.now(timezone.utc)) for e in events)),
            "status": "open",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "sample_events": [self._sanitise(e) for e in events[:5]],
        }

    # ------------------------------------------------------------------
    # Rule evaluation
    # ------------------------------------------------------------------

    def _evaluate_rule(
        self, rule: dict[str, Any], events: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Return alerts generated by evaluating *rule* against *events*."""
        window = timedelta(seconds=rule["window_seconds"])
        now = datetime.now(timezone.utc)
        cutoff = now - window

        # Filter events to those within the window and matching the rule
        candidate_events = [
            e for e in events
            if e.get("_corr_ts", now) >= cutoff and self._matches_filter(e, rule["event_filter"])
        ]

        if not candidate_events:
            return []

        group_by = rule.get("group_by", "source_ip")
        groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for evt in candidate_events:
            key = str(evt.get(group_by) or "unknown")
            groups[key].append(evt)

        alerts: list[dict[str, Any]] = []
        for group_val, group_events in groups.items():
            if not self._threshold_met(rule, group_events):
                continue
            if self._is_duplicate(rule["id"], group_val, now):
                continue
            alert = self.generate_alert(group_events, rule)
            alert["group_value"] = group_val
            alerts.append(alert)
            self._dedup_index[rule["id"]][group_val] = now

        return alerts

    def _matches_filter(self, event: dict[str, Any], event_filter: dict[str, Any]) -> bool:
        """Return True when *event* satisfies all criteria in *event_filter*."""
        keywords: list[str] = event_filter.get("message_keywords", [])
        if keywords:
            text = " ".join(
                str(v).lower() for v in [
                    event.get("message", ""),
                    event.get("raw", ""),
                    event.get("event_type", ""),
                ]
            )
            if not any(kw.lower() in text for kw in keywords):
                return False
        if "severity" in event_filter:
            if event.get("severity") not in event_filter["severity"]:
                return False
        return True

    def _threshold_met(self, rule: dict[str, Any], events: list[dict[str, Any]]) -> bool:
        """Return True when *events* meet the numeric threshold for *rule*."""
        threshold: int = rule["threshold"]
        count_distinct_field: str | None = rule.get("count_distinct")
        anomaly_field: str | None = rule.get("anomaly")

        if anomaly_field:
            return self._detect_anomaly(events, anomaly_field)

        if count_distinct_field:
            distinct_values = {e.get(count_distinct_field) for e in events if e.get(count_distinct_field)}
            return len(distinct_values) >= threshold

        return len(events) >= threshold

    def _detect_anomaly(self, events: list[dict[str, Any]], field: str) -> bool:
        """
        Modified z-score (MAD-based) anomaly detection for a numeric *field*.

        Uses the median absolute deviation (MAD) rather than the standard
        deviation so that a single extreme value does not mask itself by
        inflating the mean and stdev.  A modified z-score threshold of 3.5
        is applied (Iglewicz & Hoaglin, 1993).

        Returns True when any value exceeds the threshold, or when data is
        very sparse (≤ 1 observation).
        """
        values: list[float] = []
        for evt in events:
            raw = evt.get(field) or evt.get("extra", {}).get(field)
            try:
                values.append(float(raw))  # type: ignore[arg-type]
            except (TypeError, ValueError):
                continue

        if len(values) < 2:
            return len(values) >= 1  # sparse data: flag if at least one data point

        med = statistics.median(values)
        abs_deviations = [abs(v - med) for v in values]
        mad = statistics.median(abs_deviations)

        if mad == 0:
            # Fall back to mean-absolute-deviation when MAD is zero
            mad = statistics.mean(abs_deviations) or 1e-9

        modified_z_scores = [0.6745 * abs(v - med) / mad for v in values]
        return any(z > 3.5 for z in modified_z_scores)

    def _is_duplicate(self, rule_id: str, group_val: str, now: datetime) -> bool:
        """Return True when this rule/group combination fired recently."""
        last_fired = self._dedup_index.get(rule_id, {}).get(group_val)
        if last_fired is None:
            return False
        return (now - last_fired) < self._dedup_window

    # ------------------------------------------------------------------
    # Pattern matching helpers (used by external callers)
    # ------------------------------------------------------------------

    def detect_sequential_pattern(
        self,
        events: list[dict[str, Any]],
        pattern: list[str],
        field: str = "event_type",
        window_seconds: int = 300,
    ) -> list[list[dict[str, Any]]]:
        """
        Find all occurrences of an ordered *pattern* of field values within
        *window_seconds* in *events*.

        Parameters
        ----------
        events:
            Ordered list of events (oldest first).
        pattern:
            Ordered list of expected field values.
        field:
            The event field to match against.
        window_seconds:
            Maximum time span across which the pattern must complete.

        Returns
        -------
        list
            List of matched event sub-sequences.
        """
        if not pattern:
            return []

        matches: list[list[dict[str, Any]]] = []
        window = timedelta(seconds=window_seconds)

        for start_idx, evt in enumerate(events):
            if str(evt.get(field, "")).lower() != pattern[0].lower():
                continue
            # Try to match the rest of the pattern from this starting event
            seq: list[dict[str, Any]] = [evt]
            pattern_pos = 1
            start_ts: datetime = evt.get("_corr_ts", datetime.now(timezone.utc))

            for candidate in events[start_idx + 1:]:
                cand_ts: datetime = candidate.get("_corr_ts", datetime.now(timezone.utc))
                if (cand_ts - start_ts) > window:
                    break
                if str(candidate.get(field, "")).lower() == pattern[pattern_pos].lower():
                    seq.append(candidate)
                    pattern_pos += 1
                    if pattern_pos == len(pattern):
                        matches.append(seq)
                        break

        return matches

    def calculate_risk_score(self, alerts: list[dict[str, Any]]) -> float:
        """
        Calculate a composite risk score (0–100) from a list of alerts.

        The score is influenced by alert severity and recency.
        """
        if not alerts:
            return 0.0

        severity_weights = {"critical": 40, "high": 20, "medium": 10, "low": 5, "info": 1}
        total = 0.0
        for alert in alerts:
            weight = severity_weights.get(alert.get("severity", "info"), 1)
            total += weight

        # Sigmoid-like normalisation so score stays ≤ 100
        score = 100 * (1 - math.exp(-total / 50))
        return round(score, 2)

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    @staticmethod
    def _ts_str(dt: datetime) -> str:
        return dt.isoformat() if hasattr(dt, "isoformat") else str(dt)

    @staticmethod
    def _sanitise(event: dict[str, Any]) -> dict[str, Any]:
        """Remove internal keys (prefixed with '_') before including in alerts."""
        return {k: v for k, v in event.items() if not k.startswith("_")}
