"""
Incident Response Module
Executes automated response playbooks for common SIEM alert types.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Callable

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Type alias
# ---------------------------------------------------------------------------
PlaybookFn = Callable[["IncidentResponse", dict[str, Any]], dict[str, Any]]


class IncidentResponse:
    """
    Automated incident response playbook executor.

    Built-in playbooks handle common scenarios:
        - ``brute_force``        – block offending IP, lock user account
        - ``malware``            – isolate host, collect artefacts
        - ``data_exfiltration``  – block egress, preserve evidence
        - ``containment``        – generic containment steps
        - ``isolation``          – host isolation
        - ``notification``       – stakeholder notification

    Custom playbooks can be registered with :meth:`register_playbook`.
    All actions are written to an in-memory audit trail accessible via
    :meth:`get_audit_log`.
    """

    def __init__(self):
        self._audit_trail: list[dict[str, Any]] = []
        # Maps playbook name → method
        self._registry: dict[str, PlaybookFn] = {
            "brute_force": IncidentResponse.brute_force_playbook,
            "malware": IncidentResponse.malware_playbook,
            "data_exfiltration": IncidentResponse.data_exfiltration_playbook,
            "containment": IncidentResponse.containment_playbook,
            "isolation": IncidentResponse.isolation_playbook,
            "notification": IncidentResponse.notification_playbook,
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def register_playbook(self, name: str, fn: PlaybookFn) -> None:
        """
        Register a custom playbook function under *name*.

        The function must accept ``(self, context: dict)`` and return a
        result dict.

        Parameters
        ----------
        name:
            Unique identifier for the playbook.
        fn:
            Callable implementing the playbook logic.
        """
        self._registry[name] = fn
        logger.info("Registered custom playbook: %s", name)

    def execute_playbook(self, playbook_name: str, context: dict[str, Any]) -> dict[str, Any]:
        """
        Execute a named playbook with the given *context*.

        Parameters
        ----------
        playbook_name:
            The name of the playbook to execute.
        context:
            Contextual data available to the playbook (alert dict, IPs,
            users, hostnames, etc.).

        Returns
        -------
        dict
            Execution summary produced by the playbook.

        Raises
        ------
        ValueError
            When *playbook_name* is not registered.
        """
        fn = self._registry.get(playbook_name)
        if fn is None:
            available = ", ".join(sorted(self._registry.keys()))
            raise ValueError(
                f"Unknown playbook '{playbook_name}'. Available: {available}"
            )

        execution_id = str(uuid.uuid4())
        logger.info("Executing playbook '%s' (execution_id=%s)", playbook_name, execution_id)

        result: dict[str, Any] = {
            "execution_id": execution_id,
            "playbook": playbook_name,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "status": "running",
            "actions": [],
        }

        try:
            playbook_result = fn(self, context)
            result.update(playbook_result)
            result["status"] = "completed"
        except Exception as exc:
            logger.error("Playbook '%s' failed: %s", playbook_name, exc, exc_info=True)
            result["status"] = "failed"
            result["error"] = str(exc)
        finally:
            result["finished_at"] = datetime.now(timezone.utc).isoformat()

        self.audit_log(
            action=f"playbook:{playbook_name}",
            context={"execution_id": execution_id, "status": result["status"], **context},
        )
        return result

    def audit_log(self, action: str, context: dict[str, Any]) -> None:
        """
        Append an entry to the in-memory audit trail.

        Parameters
        ----------
        action:
            A short description of the action taken.
        context:
            Contextual data associated with the action.
        """
        entry: dict[str, Any] = {
            "audit_id": str(uuid.uuid4()),
            "action": action,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "context": context,
        }
        self._audit_trail.append(entry)
        logger.info("AUDIT: %s | context keys: %s", action, list(context.keys()))

    def get_audit_log(self) -> list[dict[str, Any]]:
        """Return a copy of the full audit trail (newest entry last)."""
        return list(self._audit_trail)

    def list_playbooks(self) -> list[str]:
        """Return the names of all registered playbooks."""
        return sorted(self._registry.keys())

    # ------------------------------------------------------------------
    # Built-in playbooks
    # ------------------------------------------------------------------

    def brute_force_playbook(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        Respond to a brute-force authentication alert.

        Steps:
            1. Block offending source IPs at the firewall.
            2. Lock compromised / targeted user accounts.
            3. Invalidate active sessions for affected users.
            4. Send security team notification.
            5. Create a forensic timeline entry.
        """
        actions: list[dict[str, Any]] = []
        source_ips: list[str] = context.get("source_ips", [])
        users: list[str] = context.get("users", [])

        for ip in source_ips:
            actions.append(self._action("block_ip", {"ip": ip, "reason": "brute_force", "duration_hours": 24}))
        for user in users:
            actions.append(self._action("lock_account", {"user": user, "reason": "brute_force_target"}))
            actions.append(self._action("invalidate_sessions", {"user": user}))

        actions.append(
            self._action(
                "send_notification",
                {
                    "channel": "security_team",
                    "message": f"Brute force detected from {source_ips}; accounts locked: {users}",
                    "severity": "high",
                },
            )
        )
        actions.append(self._action("create_timeline_entry", {"event": "brute_force_response", "context": context}))

        return {
            "actions": actions,
            "blocked_ips": source_ips,
            "locked_accounts": users,
            "summary": f"Blocked {len(source_ips)} IPs and locked {len(users)} accounts.",
        }

    def malware_playbook(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        Respond to a malware detection alert.

        Steps:
            1. Isolate affected hosts from the network.
            2. Snapshot host memory and disk (forensic preservation).
            3. Revoke credentials for affected users.
            4. Trigger AV/EDR scan on adjacent hosts.
            5. Notify IR team and management.
        """
        actions: list[dict[str, Any]] = []
        hostnames: list[str] = context.get("hostnames", [])
        users: list[str] = context.get("users", [])

        for host in hostnames:
            actions.append(self._action("isolate_host", {"hostname": host, "reason": "malware_detected"}))
            actions.append(self._action("snapshot_host", {"hostname": host, "type": "full"}))
            actions.append(self._action("trigger_av_scan", {"hostname": host, "scope": "full"}))

        for user in users:
            actions.append(self._action("revoke_credentials", {"user": user, "reason": "malware_compromise"}))

        actions.append(
            self._action(
                "send_notification",
                {
                    "channel": "ir_team",
                    "message": f"Malware detected on {hostnames}; hosts isolated.",
                    "severity": "critical",
                },
            )
        )
        return {
            "actions": actions,
            "isolated_hosts": hostnames,
            "revoked_users": users,
            "summary": f"Isolated {len(hostnames)} hosts; revoked credentials for {len(users)} users.",
        }

    def data_exfiltration_playbook(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        Respond to a suspected data exfiltration alert.

        Steps:
            1. Block outbound traffic from offending hosts.
            2. Capture network traffic for evidence.
            3. Disable accounts involved.
            4. Preserve log evidence.
            5. Notify DLP team and management.
        """
        actions: list[dict[str, Any]] = []
        source_ips: list[str] = context.get("source_ips", [])
        hostnames: list[str] = context.get("hostnames", [])
        users: list[str] = context.get("users", [])

        for ip in source_ips:
            actions.append(self._action("block_egress", {"ip": ip, "reason": "data_exfiltration"}))
            actions.append(self._action("capture_traffic", {"ip": ip, "duration_minutes": 30}))

        for host in hostnames:
            actions.append(self._action("preserve_logs", {"hostname": host, "retention_days": 90}))

        for user in users:
            actions.append(self._action("disable_account", {"user": user, "reason": "data_exfiltration_suspect"}))

        actions.append(
            self._action(
                "send_notification",
                {
                    "channel": "dlp_team",
                    "message": f"Data exfiltration suspected from {source_ips}; egress blocked.",
                    "severity": "critical",
                },
            )
        )
        return {
            "actions": actions,
            "blocked_egress": source_ips,
            "disabled_accounts": users,
            "summary": f"Blocked egress for {len(source_ips)} IPs; disabled {len(users)} accounts.",
        }

    def containment_playbook(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        Generic containment: block IPs and disable accounts.
        """
        actions: list[dict[str, Any]] = []
        source_ips: list[str] = context.get("source_ips", [])
        users: list[str] = context.get("users", [])

        for ip in source_ips:
            actions.append(self._action("block_ip", {"ip": ip, "reason": "containment"}))
        for user in users:
            actions.append(self._action("disable_account", {"user": user, "reason": "containment"}))

        return {
            "actions": actions,
            "summary": f"Containment applied: {len(source_ips)} IPs blocked, {len(users)} accounts disabled.",
        }

    def isolation_playbook(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        Network-isolate one or more hosts.
        """
        actions: list[dict[str, Any]] = []
        hostnames: list[str] = context.get("hostnames", [])

        for host in hostnames:
            actions.append(self._action("isolate_host", {"hostname": host, "reason": "manual_isolation"}))
            actions.append(self._action("block_all_traffic", {"hostname": host, "except": ["management_vlan"]}))

        return {
            "actions": actions,
            "isolated_hosts": hostnames,
            "summary": f"Isolated {len(hostnames)} host(s).",
        }

    def notification_playbook(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        Send notifications to configured stakeholder channels.
        """
        actions: list[dict[str, Any]] = []
        message: str = context.get("message", "Security event detected. Please investigate.")
        severity: str = context.get("severity", "medium")
        channels: list[str] = context.get("channels", ["security_team", "soc"])

        for channel in channels:
            actions.append(
                self._action(
                    "send_notification",
                    {"channel": channel, "message": message, "severity": severity},
                )
            )

        return {
            "actions": actions,
            "notified_channels": channels,
            "summary": f"Notifications sent to {len(channels)} channel(s).",
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _action(self, action_type: str, params: dict[str, Any]) -> dict[str, Any]:
        """
        Record and simulate a single response action.

        In production this would call real integrations (firewall API,
        AD/LDAP, SOAR platform, etc.).  Here it logs the action and
        returns a simulated success result.
        """
        action: dict[str, Any] = {
            "action_id": str(uuid.uuid4()),
            "type": action_type,
            "params": params,
            "executed_at": datetime.now(timezone.utc).isoformat(),
            "status": "simulated",  # Change to "success"/"failed" with real integrations
            "result": f"[SIMULATED] {action_type} executed with params: {params}",
        }
        logger.info("IR action: %s → %s", action_type, params)
        return action
