"""
Threat Intelligence Module
Provides IP, domain, file-hash, and CVE reputation lookups backed by a
local MongoDB feed database and mock data for demonstration purposes.
"""

import hashlib
import ipaddress
import logging
import os
import re
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Static mock threat feeds (used when MongoDB is unavailable)
# ---------------------------------------------------------------------------
_MOCK_MALICIOUS_IPS: dict[str, dict[str, Any]] = {
    "185.220.101.1": {
        "ip": "185.220.101.1",
        "reputation": "malicious",
        "category": ["tor_exit_node", "spam"],
        "confidence": 95,
        "last_seen": "2024-06-01",
        "asn": "AS0",
        "country": "DE",
        "source": "mock_feed",
    },
    "45.33.32.156": {
        "ip": "45.33.32.156",
        "reputation": "suspicious",
        "category": ["scanner"],
        "confidence": 75,
        "last_seen": "2024-05-28",
        "asn": "AS63949",
        "country": "US",
        "source": "mock_feed",
    },
    "198.51.100.99": {
        "ip": "198.51.100.99",
        "reputation": "malicious",
        "category": ["botnet_c2", "malware"],
        "confidence": 98,
        "last_seen": "2024-06-03",
        "asn": "AS0",
        "country": "RU",
        "source": "mock_feed",
    },
}

_MOCK_MALICIOUS_DOMAINS: dict[str, dict[str, Any]] = {
    "evil-malware.example.com": {
        "domain": "evil-malware.example.com",
        "reputation": "malicious",
        "category": ["malware_distribution"],
        "confidence": 99,
        "source": "mock_feed",
    },
    "phish-login.example.net": {
        "domain": "phish-login.example.net",
        "reputation": "malicious",
        "category": ["phishing"],
        "confidence": 90,
        "source": "mock_feed",
    },
    "ad-tracker.example.org": {
        "domain": "ad-tracker.example.org",
        "reputation": "suspicious",
        "category": ["adware", "tracking"],
        "confidence": 60,
        "source": "mock_feed",
    },
}

_MOCK_MALICIOUS_HASHES: dict[str, dict[str, Any]] = {
    "44d88612fea8a8f36de82e1278abb02f": {
        "hash": "44d88612fea8a8f36de82e1278abb02f",
        "type": "md5",
        "reputation": "malicious",
        "malware_family": "Mirai",
        "confidence": 100,
        "source": "mock_feed",
    },
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855": {
        "hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "type": "sha256",
        "reputation": "clean",
        "note": "Empty file hash",
        "confidence": 100,
        "source": "mock_feed",
    },
}

_MOCK_CVES: dict[str, dict[str, Any]] = {
    "CVE-2021-44228": {
        "cve_id": "CVE-2021-44228",
        "description": "Apache Log4j2 JNDI remote code execution vulnerability (Log4Shell).",
        "cvss_score": 10.0,
        "severity": "critical",
        "affected_products": ["Apache Log4j2 2.0-beta9 through 2.14.1"],
        "patch_available": True,
        "exploited_in_wild": True,
        "source": "mock_feed",
    },
    "CVE-2022-26134": {
        "cve_id": "CVE-2022-26134",
        "description": "Atlassian Confluence Server OGNL injection.",
        "cvss_score": 9.8,
        "severity": "critical",
        "affected_products": ["Confluence Server", "Confluence Data Center"],
        "patch_available": True,
        "exploited_in_wild": True,
        "source": "mock_feed",
    },
    "CVE-2023-44487": {
        "cve_id": "CVE-2023-44487",
        "description": "HTTP/2 Rapid Reset DDoS vulnerability.",
        "cvss_score": 7.5,
        "severity": "high",
        "affected_products": ["Multiple HTTP/2 implementations"],
        "patch_available": True,
        "exploited_in_wild": True,
        "source": "mock_feed",
    },
}

# Severity weight used for risk score calculation
_REPUTATION_WEIGHT = {"malicious": 1.0, "suspicious": 0.5, "clean": 0.0, "unknown": 0.1}
_SEVERITY_CVSS = {"critical": 1.0, "high": 0.75, "medium": 0.5, "low": 0.25, "info": 0.1}


class ThreatIntel:
    """
    Threat Intelligence lookup service.

    Checks indicators of compromise (IoC) against a local feed database
    stored in MongoDB, falling back to built-in mock data when the
    database is unavailable.
    """

    def __init__(self, mongo_db=None):
        """
        Parameters
        ----------
        mongo_db:
            An optional PyMongo database object.  When provided, lookups
            are first attempted against the ``threat_feeds`` collection.
        """
        self._db = mongo_db

    # ------------------------------------------------------------------
    # Public lookup methods
    # ------------------------------------------------------------------

    def check_ip(self, ip: str) -> dict[str, Any]:
        """
        Look up the reputation of *ip*.

        Returns a dict with keys: ip, reputation, confidence, category,
        country, asn, source.  ``reputation`` is one of
        ``'malicious'``, ``'suspicious'``, ``'clean'``, ``'unknown'``.
        """
        ip = ip.strip()
        if not self._is_valid_ip(ip):
            return {"ip": ip, "reputation": "unknown", "error": "Invalid IP address format"}

        # Private / reserved ranges are always safe
        if self._is_private_ip(ip):
            return {"ip": ip, "reputation": "clean", "note": "Private / RFC-1918 address", "confidence": 100}

        # MongoDB lookup
        if self._db is not None:
            try:
                doc = self._db.threat_feeds.find_one({"type": "ip", "value": ip})
                if doc:
                    doc.pop("_id", None)
                    return doc
            except Exception as exc:
                logger.warning("MongoDB IP lookup failed: %s", exc)

        # Mock fallback
        return _MOCK_MALICIOUS_IPS.get(
            ip,
            {"ip": ip, "reputation": "unknown", "confidence": 0, "source": "no_data"},
        )

    def check_domain(self, domain: str) -> dict[str, Any]:
        """
        Look up the reputation of *domain*.

        Returns a dict with keys: domain, reputation, confidence, category, source.
        """
        domain = domain.strip().lower()
        if not self._is_valid_domain(domain):
            return {"domain": domain, "reputation": "unknown", "error": "Invalid domain format"}

        if self._db is not None:
            try:
                doc = self._db.threat_feeds.find_one({"type": "domain", "value": domain})
                if doc:
                    doc.pop("_id", None)
                    return doc
            except Exception as exc:
                logger.warning("MongoDB domain lookup failed: %s", exc)

        return _MOCK_MALICIOUS_DOMAINS.get(
            domain,
            {"domain": domain, "reputation": "unknown", "confidence": 0, "source": "no_data"},
        )

    def check_hash(self, file_hash: str) -> dict[str, Any]:
        """
        Look up the reputation of a file hash (MD5 / SHA-1 / SHA-256).

        Returns a dict with keys: hash, type, reputation, malware_family,
        confidence, source.
        """
        file_hash = file_hash.strip().lower()
        hash_type = self._classify_hash(file_hash)
        if hash_type is None:
            return {"hash": file_hash, "reputation": "unknown", "error": "Unrecognised hash format"}

        if self._db is not None:
            try:
                doc = self._db.threat_feeds.find_one({"type": "hash", "value": file_hash})
                if doc:
                    doc.pop("_id", None)
                    return doc
            except Exception as exc:
                logger.warning("MongoDB hash lookup failed: %s", exc)

        return _MOCK_MALICIOUS_HASHES.get(
            file_hash,
            {
                "hash": file_hash,
                "type": hash_type,
                "reputation": "unknown",
                "confidence": 0,
                "source": "no_data",
            },
        )

    def check_cve(self, cve_id: str) -> dict[str, Any]:
        """
        Retrieve CVE details and exploitability information for *cve_id*.

        Returns a dict with keys: cve_id, description, cvss_score,
        severity, affected_products, patch_available, exploited_in_wild.
        """
        cve_id = cve_id.strip().upper()
        if not re.match(r"^CVE-\d{4}-\d{4,}$", cve_id):
            return {"cve_id": cve_id, "error": "Invalid CVE ID format"}

        if self._db is not None:
            try:
                doc = self._db.cves.find_one({"cve_id": cve_id})
                if doc:
                    doc.pop("_id", None)
                    return doc
            except Exception as exc:
                logger.warning("MongoDB CVE lookup failed: %s", exc)

        return _MOCK_CVES.get(
            cve_id,
            {"cve_id": cve_id, "severity": "unknown", "cvss_score": None, "source": "no_data"},
        )

    def calculate_risk_score(self, indicators: list[dict[str, Any]]) -> float:
        """
        Compute an overall risk score (0–100) from a list of indicator results.

        The score accounts for the reputation of each indicator and, for
        CVEs, the CVSS base score.

        Parameters
        ----------
        indicators:
            List of dicts as returned by :meth:`check_ip`, :meth:`check_domain`,
            :meth:`check_hash`, or :meth:`check_cve`.

        Returns
        -------
        float
            A score in the range [0, 100].
        """
        if not indicators:
            return 0.0

        total_weight = 0.0
        for indicator in indicators:
            if not isinstance(indicator, dict):
                continue
            reputation = indicator.get("reputation", "unknown")
            confidence = float(indicator.get("confidence", 0)) / 100.0
            base_weight = _REPUTATION_WEIGHT.get(reputation, 0.1)

            # For CVEs, use CVSS score as an additional multiplier
            cvss = indicator.get("cvss_score")
            if cvss is not None:
                try:
                    cvss_multiplier = float(cvss) / 10.0
                    base_weight = max(base_weight, _SEVERITY_CVSS.get(indicator.get("severity", "info"), 0.1))
                    base_weight = (base_weight + cvss_multiplier) / 2
                except (TypeError, ValueError):
                    pass

            total_weight += base_weight * max(confidence, 0.1)

        # Normalise to [0, 100]
        score = min(100.0, total_weight * 100 / max(len(indicators), 1))
        return round(score, 2)

    def get_all_feeds(self) -> dict[str, Any]:
        """
        Return summary statistics about all threat feeds in the database.

        Falls back to returning mock feed metadata when MongoDB is unavailable.
        """
        if self._db is not None:
            try:
                pipeline = [
                    {"$group": {"_id": "$type", "count": {"$sum": 1}, "last_updated": {"$max": "$updated_at"}}},
                ]
                results = list(self._db.threat_feeds.aggregate(pipeline))
                return {
                    "feeds": results,
                    "total": sum(r["count"] for r in results),
                    "source": "mongodb",
                    "retrieved_at": datetime.now(timezone.utc).isoformat(),
                }
            except Exception as exc:
                logger.warning("MongoDB feed summary failed: %s", exc)

        return {
            "feeds": [
                {"_id": "ip", "count": len(_MOCK_MALICIOUS_IPS), "last_updated": "2024-06-03"},
                {"_id": "domain", "count": len(_MOCK_MALICIOUS_DOMAINS), "last_updated": "2024-06-03"},
                {"_id": "hash", "count": len(_MOCK_MALICIOUS_HASHES), "last_updated": "2024-06-03"},
                {"_id": "cve", "count": len(_MOCK_CVES), "last_updated": "2024-06-03"},
            ],
            "total": len(_MOCK_MALICIOUS_IPS) + len(_MOCK_MALICIOUS_DOMAINS) + len(_MOCK_MALICIOUS_HASHES) + len(_MOCK_CVES),
            "source": "mock",
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
        }

    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _is_valid_ip(ip: str) -> bool:
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False

    @staticmethod
    def _is_private_ip(ip: str) -> bool:
        try:
            return ipaddress.ip_address(ip).is_private
        except ValueError:
            return False

    @staticmethod
    def _is_valid_domain(domain: str) -> bool:
        pattern = re.compile(
            r"^(?:[a-zA-Z0-9]"
            r"(?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?"
            r"\.)+[a-zA-Z]{2,}$"
        )
        return bool(pattern.match(domain)) and len(domain) <= 253

    @staticmethod
    def _classify_hash(file_hash: str) -> str | None:
        length_map = {32: "md5", 40: "sha1", 64: "sha256", 128: "sha512"}
        return length_map.get(len(file_hash))
