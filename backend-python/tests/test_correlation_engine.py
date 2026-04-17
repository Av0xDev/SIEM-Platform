"""
Unit tests for the CorrelationEngine module.
"""

import time
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from modules.correlation_engine import CorrelationEngine


@pytest.fixture
def engine():
    return CorrelationEngine(dedup_window_seconds=0)  # disable dedup for most tests


@pytest.fixture
def engine_with_dedup():
    return CorrelationEngine(dedup_window_seconds=300)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _make_event(
    message="test event",
    source_ip="1.2.3.4",
    severity="info",
    event_type="generic",
    user=None,
    hostname="host01",
    age_seconds=0,
) -> dict:
    ts = datetime.now(timezone.utc) - timedelta(seconds=age_seconds)
    return {
        "message": message,
        "source_ip": source_ip,
        "severity": severity,
        "event_type": event_type,
        "user": user,
        "hostname": hostname,
        "_corr_ts": ts,
    }


# ---------------------------------------------------------------------------
# add_event / basic storage
# ---------------------------------------------------------------------------
class TestAddEvent:
    def test_event_stored(self, engine):
        evt = _make_event()
        engine.add_event(evt)
        assert len(list(engine._events)) == 1

    def test_corr_ts_injected_if_missing(self, engine):
        evt = {"message": "no ts"}
        engine.add_event(evt)
        stored = list(engine._events)[0]
        assert "_corr_ts" in stored

    def test_multiple_events_stored(self, engine):
        for _ in range(10):
            engine.add_event(_make_event())
        assert len(list(engine._events)) == 10

    def test_maxlen_respected(self):
        small_engine = CorrelationEngine(max_events=3)
        for i in range(5):
            small_engine.add_event(_make_event(source_ip=f"10.0.0.{i}"))
        assert len(list(small_engine._events)) == 3


# ---------------------------------------------------------------------------
# correlate – brute force rule
# ---------------------------------------------------------------------------
class TestBruteForceRule:
    def _load_failed_logins(self, engine, count=6, source_ip="10.0.0.1"):
        for _ in range(count):
            engine.add_event(
                _make_event(
                    message="Failed password for root from 10.0.0.1",
                    source_ip=source_ip,
                )
            )

    def test_alert_generated_above_threshold(self, engine):
        self._load_failed_logins(engine)
        alerts = engine.correlate()
        rule_ids = [a["rule_id"] for a in alerts]
        assert "brute_force" in rule_ids

    def test_no_alert_below_threshold(self, engine):
        self._load_failed_logins(engine, count=3)
        alerts = engine.correlate()
        rule_ids = [a["rule_id"] for a in alerts]
        assert "brute_force" not in rule_ids

    def test_alert_contains_source_ip(self, engine):
        self._load_failed_logins(engine, source_ip="192.168.5.5")
        alerts = engine.correlate()
        bf_alerts = [a for a in alerts if a["rule_id"] == "brute_force"]
        assert bf_alerts
        assert "192.168.5.5" in bf_alerts[0]["source_ips"]

    def test_alert_severity_is_high(self, engine):
        self._load_failed_logins(engine)
        alerts = engine.correlate()
        bf = next((a for a in alerts if a["rule_id"] == "brute_force"), None)
        assert bf is not None
        assert bf["severity"] == "high"

    def test_alert_has_required_keys(self, engine):
        self._load_failed_logins(engine)
        alerts = engine.correlate()
        bf = next(a for a in alerts if a["rule_id"] == "brute_force")
        for key in ("alert_id", "rule_id", "rule_name", "severity", "event_count", "created_at"):
            assert key in bf, f"Missing key: {key}"

    def test_events_outside_window_not_counted(self):
        eng = CorrelationEngine(dedup_window_seconds=0)
        for _ in range(6):
            evt = _make_event(
                message="Failed password for root",
                source_ip="10.0.0.1",
                age_seconds=999_999,  # far outside the 5-min window
            )
            eng.add_event(evt)
        alerts = eng.correlate()
        rule_ids = [a["rule_id"] for a in alerts]
        assert "brute_force" not in rule_ids


# ---------------------------------------------------------------------------
# correlate – port scan rule
# ---------------------------------------------------------------------------
class TestPortScanRule:
    def test_alert_generated_for_many_distinct_ports(self, engine):
        for port in range(25):
            engine.add_event(
                _make_event(
                    message="connection refused port syn connect",
                    source_ip="10.1.1.1",
                    event_type="network",
                )
            )
            # Simulate distinct dest_port field on each event
            list(engine._events)[-1]["dest_port"] = str(port)

        alerts = engine.correlate()
        rule_ids = [a["rule_id"] for a in alerts]
        assert "port_scan" in rule_ids


# ---------------------------------------------------------------------------
# Alert deduplication
# ---------------------------------------------------------------------------
class TestDeduplication:
    def test_second_alert_suppressed_within_window(self, engine_with_dedup):
        for _ in range(6):
            engine_with_dedup.add_event(
                _make_event(message="Failed password for root", source_ip="10.0.0.1")
            )
        alerts_first = engine_with_dedup.correlate()
        bf_first = [a for a in alerts_first if a["rule_id"] == "brute_force"]
        assert bf_first

        # Add more events and correlate again — should be suppressed
        for _ in range(6):
            engine_with_dedup.add_event(
                _make_event(message="Failed password for root", source_ip="10.0.0.1")
            )
        alerts_second = engine_with_dedup.correlate()
        bf_second = [a for a in alerts_second if a["rule_id"] == "brute_force"]
        assert not bf_second, "Expected second alert to be deduplicated"


# ---------------------------------------------------------------------------
# generate_alert
# ---------------------------------------------------------------------------
class TestGenerateAlert:
    RULE = {
        "id": "test_rule",
        "name": "Test Rule",
        "description": "A test rule",
        "severity": "medium",
        "tactic": "Test Tactic",
        "technique": "T9999",
    }

    def test_returns_dict(self, engine):
        events = [_make_event(source_ip="1.2.3.4", user="alice", hostname="host01")]
        alert = engine.generate_alert(events, self.RULE)
        assert isinstance(alert, dict)

    def test_rule_metadata_present(self, engine):
        events = [_make_event()]
        alert = engine.generate_alert(events, self.RULE)
        assert alert["rule_id"] == "test_rule"
        assert alert["rule_name"] == "Test Rule"
        assert alert["severity"] == "medium"

    def test_source_ips_deduplicated(self, engine):
        events = [
            _make_event(source_ip="1.2.3.4"),
            _make_event(source_ip="1.2.3.4"),
            _make_event(source_ip="5.6.7.8"),
        ]
        alert = engine.generate_alert(events, self.RULE)
        assert len(alert["source_ips"]) == 2

    def test_event_count_correct(self, engine):
        events = [_make_event() for _ in range(7)]
        alert = engine.generate_alert(events, self.RULE)
        assert alert["event_count"] == 7

    def test_sample_events_capped_at_five(self, engine):
        events = [_make_event() for _ in range(20)]
        alert = engine.generate_alert(events, self.RULE)
        assert len(alert["sample_events"]) == 5

    def test_internal_keys_removed_from_samples(self, engine):
        events = [_make_event()]
        alert = engine.generate_alert(events, self.RULE)
        for sample in alert["sample_events"]:
            for key in sample:
                assert not key.startswith("_"), f"Internal key found in sample: {key}"

    def test_alert_id_is_unique(self, engine):
        events = [_make_event()]
        id1 = engine.generate_alert(events, self.RULE)["alert_id"]
        id2 = engine.generate_alert(events, self.RULE)["alert_id"]
        assert id1 != id2


# ---------------------------------------------------------------------------
# get_recent_alerts
# ---------------------------------------------------------------------------
class TestGetRecentAlerts:
    def test_returns_list(self, engine):
        assert isinstance(engine.get_recent_alerts(), list)

    def test_alerts_appear_after_correlate(self, engine):
        for _ in range(6):
            engine.add_event(_make_event(message="Failed password for root"))
        engine.correlate()
        alerts = engine.get_recent_alerts()
        assert len(alerts) > 0

    def test_returns_copy_not_reference(self, engine):
        original = engine.get_recent_alerts()
        original.append({"fake": "alert"})
        assert len(engine.get_recent_alerts()) == 0


# ---------------------------------------------------------------------------
# Sequential pattern detection
# ---------------------------------------------------------------------------
class TestSequentialPatternDetection:
    def test_detects_simple_sequence(self, engine):
        events = [
            _make_event(event_type="login"),
            _make_event(event_type="privilege_escalation"),
            _make_event(event_type="data_access"),
        ]
        matches = engine.detect_sequential_pattern(
            events, ["login", "privilege_escalation", "data_access"]
        )
        assert len(matches) == 1

    def test_returns_empty_for_no_match(self, engine):
        events = [_make_event(event_type="login"), _make_event(event_type="logout")]
        matches = engine.detect_sequential_pattern(
            events, ["login", "privilege_escalation", "data_access"]
        )
        assert matches == []

    def test_returns_empty_for_empty_pattern(self, engine):
        events = [_make_event(event_type="login")]
        matches = engine.detect_sequential_pattern(events, [])
        assert matches == []

    def test_pattern_outside_window_not_matched(self, engine):
        events = [
            _make_event(event_type="login", age_seconds=400),
            _make_event(event_type="data_access", age_seconds=0),
        ]
        matches = engine.detect_sequential_pattern(
            events, ["login", "data_access"], window_seconds=300
        )
        assert matches == []

    def test_case_insensitive_matching(self, engine):
        events = [_make_event(event_type="LOGIN"), _make_event(event_type="DATA_ACCESS")]
        matches = engine.detect_sequential_pattern(events, ["login", "data_access"])
        assert len(matches) == 1


# ---------------------------------------------------------------------------
# Anomaly detection
# ---------------------------------------------------------------------------
class TestAnomalyDetection:
    def test_detects_outlier_above_3_sigma(self, engine):
        # 9 normal values + 1 extreme outlier
        events = [{"bytes_out": float(v)} for v in [100, 110, 90, 105, 95, 100, 102, 98, 101, 9_000_000]]
        result = engine._detect_anomaly(events, "bytes_out")
        assert result is True

    def test_no_anomaly_for_uniform_data(self, engine):
        events = [{"bytes_out": 100.0} for _ in range(10)]
        result = engine._detect_anomaly(events, "bytes_out")
        assert result is False

    def test_handles_missing_field(self, engine):
        events = [{"other_field": 1} for _ in range(10)]
        result = engine._detect_anomaly(events, "bytes_out")
        assert result is False

    def test_single_event_returns_true(self, engine):
        events = [{"bytes_out": 500.0}]
        result = engine._detect_anomaly(events, "bytes_out")
        assert result is True


# ---------------------------------------------------------------------------
# Risk score calculation
# ---------------------------------------------------------------------------
class TestRiskScore:
    def test_empty_list_returns_zero(self, engine):
        assert engine.calculate_risk_score([]) == 0.0

    def test_critical_alerts_produce_high_score(self, engine):
        alerts = [{"severity": "critical"} for _ in range(5)]
        score = engine.calculate_risk_score(alerts)
        assert score > 50

    def test_low_alerts_produce_low_score(self, engine):
        alerts = [{"severity": "low"} for _ in range(2)]
        score = engine.calculate_risk_score(alerts)
        assert score < 50

    def test_score_capped_at_100(self, engine):
        alerts = [{"severity": "critical"} for _ in range(1000)]
        score = engine.calculate_risk_score(alerts)
        assert score <= 100

    def test_score_non_negative(self, engine):
        alerts = [{"severity": "info"}]
        assert engine.calculate_risk_score(alerts) >= 0
