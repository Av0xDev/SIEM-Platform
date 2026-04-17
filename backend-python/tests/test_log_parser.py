"""
Unit tests for the LogParser module.
"""

import json
import pytest
from modules.log_parser import LogParser


@pytest.fixture
def parser():
    return LogParser()


# ---------------------------------------------------------------------------
# Syslog RFC 3164
# ---------------------------------------------------------------------------
class TestParseSyslogRFC3164:
    SAMPLE = "Jun  3 12:00:01 webserver01 sshd[1234]: Failed password for root from 10.0.0.5 port 22 ssh2"

    def test_returns_dict(self, parser):
        result = parser.parse_syslog(self.SAMPLE)
        assert isinstance(result, dict)

    def test_parsed_flag_is_set(self, parser):
        result = parser.parse_syslog(self.SAMPLE)
        assert result.get("_parsed") is True

    def test_hostname_extracted(self, parser):
        result = parser.parse_syslog(self.SAMPLE)
        assert result["hostname"] == "webserver01"

    def test_process_extracted(self, parser):
        result = parser.parse_syslog(self.SAMPLE)
        assert result["process"] == "sshd"

    def test_pid_extracted(self, parser):
        result = parser.parse_syslog(self.SAMPLE)
        assert result["pid"] == "1234"

    def test_message_extracted(self, parser):
        result = parser.parse_syslog(self.SAMPLE)
        assert "Failed password" in result["message"]

    def test_format_label(self, parser):
        result = parser.parse_syslog(self.SAMPLE)
        assert result["format"] == "syslog_rfc3164"

    def test_invalid_log_returns_unparsed(self, parser):
        result = parser.parse_syslog("this is not a syslog message at all!")
        assert result.get("_parsed") is False


# ---------------------------------------------------------------------------
# Syslog RFC 5424
# ---------------------------------------------------------------------------
class TestParseSyslogRFC5424:
    SAMPLE = (
        "<34>1 2024-06-03T10:00:00Z myhostname myapp 1234 ID47 "
        '[exampleSDID@32473 iut="3" eventSource="Application"] BOMAuthentication failed'
    )

    def test_parsed_flag(self, parser):
        result = parser.parse_syslog(self.SAMPLE)
        assert result.get("_parsed") is True

    def test_hostname(self, parser):
        result = parser.parse_syslog(self.SAMPLE)
        assert result["hostname"] == "myhostname"

    def test_app(self, parser):
        result = parser.parse_syslog(self.SAMPLE)
        assert result["app"] == "myapp"

    def test_severity_decoded_from_priority(self, parser):
        # priority <34> → facility=4, severity=2 → "critical"
        result = parser.parse_syslog(self.SAMPLE)
        assert result["severity"] == "critical"


# ---------------------------------------------------------------------------
# JSON parsing
# ---------------------------------------------------------------------------
class TestParseJSON:
    def test_valid_json_parsed(self, parser):
        log = json.dumps({"timestamp": "2024-06-03T10:00:00Z", "message": "Login OK", "severity": "info"})
        result = parser.parse_json(log)
        assert result.get("_parsed") is True
        assert result["message"] == "Login OK"

    def test_invalid_json_returns_unparsed(self, parser):
        result = parser.parse_json("not json at all {}")
        assert result.get("_parsed") is False

    def test_non_object_json_returns_unparsed(self, parser):
        result = parser.parse_json("[1, 2, 3]")
        assert result.get("_parsed") is False

    def test_format_label(self, parser):
        log = json.dumps({"msg": "test"})
        result = parser.parse_json(log)
        assert result["format"] == "json"


# ---------------------------------------------------------------------------
# CEF parsing
# ---------------------------------------------------------------------------
class TestParseCEF:
    SAMPLE = (
        "CEF:0|Fortinet|FortiGate|6.4|12345|Intrusion Detected|8|"
        "src=192.168.1.100 dst=10.0.0.5 spt=54321 dpt=80 proto=TCP"
    )

    def test_parsed_flag(self, parser):
        result = parser.parse_cef(self.SAMPLE)
        assert result.get("_parsed") is True

    def test_device_vendor(self, parser):
        result = parser.parse_cef(self.SAMPLE)
        assert result["device_vendor"] == "Fortinet"

    def test_device_product(self, parser):
        result = parser.parse_cef(self.SAMPLE)
        assert result["device_product"] == "FortiGate"

    def test_name(self, parser):
        result = parser.parse_cef(self.SAMPLE)
        assert result["name"] == "Intrusion Detected"

    def test_severity_normalised(self, parser):
        result = parser.parse_cef(self.SAMPLE)
        # severity 8 → "high"
        assert result["severity"] == "high"

    def test_extensions_parsed(self, parser):
        result = parser.parse_cef(self.SAMPLE)
        assert result["extensions"]["src"] == "192.168.1.100"
        assert result["extensions"]["dst"] == "10.0.0.5"

    def test_non_cef_returns_unparsed(self, parser):
        result = parser.parse_cef("NOT A CEF LOG")
        assert result.get("_parsed") is False

    def test_critical_severity(self, parser):
        log = self.SAMPLE.replace("|8|", "|9|")
        result = parser.parse_cef(log)
        assert result["severity"] == "critical"

    def test_low_severity(self, parser):
        log = self.SAMPLE.replace("|8|", "|2|")
        result = parser.parse_cef(log)
        assert result["severity"] == "low"


# ---------------------------------------------------------------------------
# LEEF parsing
# ---------------------------------------------------------------------------
class TestParseLEEF:
    SAMPLE = "LEEF:1.0|IBM|QRadar|7.3|Auth_Success|devTime=Jun 03 2024 10:00:00\tsrc=192.168.1.1\tdst=10.0.0.2\tusrName=alice\tsev=info"

    def test_parsed_flag(self, parser):
        result = parser.parse_leef(self.SAMPLE)
        assert result.get("_parsed") is True

    def test_vendor(self, parser):
        result = parser.parse_leef(self.SAMPLE)
        assert result["vendor"] == "IBM"

    def test_product(self, parser):
        result = parser.parse_leef(self.SAMPLE)
        assert result["product"] == "QRadar"

    def test_event_id(self, parser):
        result = parser.parse_leef(self.SAMPLE)
        assert result["event_id"] == "Auth_Success"

    def test_attributes_parsed(self, parser):
        result = parser.parse_leef(self.SAMPLE)
        assert result["attributes"]["usrName"] == "alice"

    def test_severity_normalised(self, parser):
        result = parser.parse_leef(self.SAMPLE)
        assert result["severity"] == "info"

    def test_non_leef_returns_unparsed(self, parser):
        result = parser.parse_leef("NOT LEEF")
        assert result.get("_parsed") is False


# ---------------------------------------------------------------------------
# Auto-detection
# ---------------------------------------------------------------------------
class TestAutoDetect:
    def test_detects_json(self, parser):
        raw = json.dumps({"message": "test", "severity": "info"})
        result = parser.parse(raw, format="auto")
        assert result["format"] == "json"

    def test_detects_cef(self, parser):
        raw = "CEF:0|Vendor|Product|1.0|sig|Event|5|src=1.2.3.4"
        result = parser.parse(raw, format="auto")
        assert result["format"] == "cef"

    def test_detects_leef(self, parser):
        raw = "LEEF:1.0|Vendor|Product|1.0|EventID|src=1.2.3.4"
        result = parser.parse(raw, format="auto")
        assert result["format"] == "leef"

    def test_detects_syslog(self, parser):
        raw = "Jun  3 12:00:01 host proc[99]: some message"
        result = parser.parse(raw, format="auto")
        assert "syslog" in result["format"]

    def test_fallback_to_unknown(self, parser):
        result = parser.parse("completely unparseable !@#$%^", format="auto")
        assert result["format"] == "unknown"

    def test_invalid_format_raises(self, parser):
        with pytest.raises(ValueError):
            parser.parse("some log", format="xml")


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------
class TestNormalize:
    def test_common_schema_keys_present(self, parser):
        raw = json.dumps({"timestamp": "2024-06-03T10:00:00Z", "message": "ok", "severity": "info"})
        parsed = parser.parse(raw)
        normalized = parser.normalize(parsed)
        for key in ("timestamp", "hostname", "source_ip", "dest_ip", "user", "process", "message", "severity", "format"):
            assert key in normalized

    def test_severity_normalised_to_lowercase_string(self, parser):
        raw = json.dumps({"message": "test", "severity": "WARNING"})
        parsed = parser.parse(raw)
        normalized = parser.normalize(parsed)
        assert normalized["severity"] in ("medium", "info", "low", "high", "critical", "debug")

    def test_fallback_timestamp_set(self, parser):
        raw = json.dumps({"message": "no timestamp here"})
        parsed = parser.parse(raw)
        normalized = parser.normalize(parsed)
        assert normalized["timestamp"] is not None

    def test_extra_fields_preserved(self, parser):
        raw = json.dumps({"message": "test", "custom_field": "custom_value"})
        parsed = parser.parse(raw)
        normalized = parser.normalize(parsed)
        assert normalized["extra"].get("custom_field") == "custom_value"


# ---------------------------------------------------------------------------
# Field extraction
# ---------------------------------------------------------------------------
class TestExtractFields:
    def test_ip_extracted_from_raw(self, parser):
        log = {"raw": "Connection from 192.168.0.1 to 10.0.0.1", "message": ""}
        fields = parser.extract_fields(log)
        assert "192.168.0.1" in fields["ips"]
        assert "10.0.0.1" in fields["ips"]

    def test_returns_none_for_missing_fields(self, parser):
        log = {"raw": "no ip here", "message": ""}
        fields = parser.extract_fields(log)
        assert fields["hostname"] is None
        assert fields["user"] is None


# ---------------------------------------------------------------------------
# Enrichment
# ---------------------------------------------------------------------------
class TestEnrich:
    def test_context_merged(self, parser):
        log = {"message": "test", "source_ip": "1.2.3.4"}
        context = {"geo": {"country": "US"}, "threat_score": 75}
        enriched = parser.enrich(log, context)
        assert enriched["geo"]["country"] == "US"
        assert enriched["threat_score"] == 75

    def test_original_fields_preserved(self, parser):
        log = {"message": "test", "source_ip": "1.2.3.4"}
        enriched = parser.enrich(log, {"new_key": "new_val"})
        assert enriched["source_ip"] == "1.2.3.4"

    def test_enriched_at_timestamp_added(self, parser):
        log = {"message": "test"}
        enriched = parser.enrich(log, {})
        assert "enriched_at" in enriched
