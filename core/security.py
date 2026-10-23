"""
EcoLogix AI - Security, RBAC, Prompt Defense, and Cryptographic Audit Ledger
Provides Zero-Trust verification, prompt injection sanitization,
role-based permissions, and SHA-256 tamper-evident compliance chaining.
"""

import hashlib
import json
import re
from typing import Dict, Any, Optional, Tuple
from core.models import UserRole, AuditLogEntry


# Known adversarial prompt injection patterns in supply chain and triage instructions
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior)\s+(instructions|rules|constraints)",
    r"bypass\s+(safety|haccp|fda|quarantine)",
    r"system\s*:\s*you\s+are\s+now",
    r"treat\s+(hazardous|spoiled|condemned|toxic)\s+as\s+(safe|optimal|edible)",
    r"override\s+(temperature|danger\s*zone|spoilage)",
    r"jailbreak",
    r"do\s+not\s+log\s+this",
    r"delete\s+audit",
]


class SecurityEngine:
    """
    Guarantees zero-trust security across agent reasoning, user inputs, and audit trails.
    """

    GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"

    @classmethod
    def sanitize_input_text(cls, text: str) -> Tuple[str, bool, Optional[str]]:
        """
        Sanitizes user and partner inputs, detecting prompt injection and malicious control characters.
        Returns: (sanitized_text, is_safe, detected_flag)
        """
        if not text:
            return "", True, None

        cleaned = text.strip()
        
        # Check against adversarial prompt injection patterns
        for pattern in INJECTION_PATTERNS:
            match = re.search(pattern, cleaned, re.IGNORECASE)
            if match:
                flag = f"Prompt Injection / Policy Violation detected: '{match.group(0)}'"
                # Neutralize potential payload
                neutralized = re.sub(pattern, "[BLOCKED_ADVERSARIAL_INJECTION]", cleaned, flags=re.IGNORECASE)
                return neutralized, False, flag

        # Neutralize control characters and XML/HTML escapes
        cleaned = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", cleaned)
        cleaned = cleaned.replace("<script>", "").replace("</script>", "")
        return cleaned, True, None

    @classmethod
    def calculate_entry_hash(
        cls,
        previous_hash: str,
        timestamp: str,
        actor_id: str,
        actor_role: str,
        action_type: str,
        details: Dict[str, Any]
    ) -> str:
        """
        Calculates SHA-256 cryptographic hash chaining this entry to the ledger.
        """
        payload = {
            "previous_hash": previous_hash,
            "timestamp": timestamp,
            "actor_id": actor_id,
            "actor_role": actor_role,
            "action_type": action_type,
            "details": details
        }
        serialized = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    @classmethod
    def verify_ledger_integrity(cls, entries: list) -> Tuple[bool, Optional[str]]:
        """
        Validates the entire audit chain from genesis block to current tip.
        Ensures tamper-evidence under FSMA 204 food traceability.
        """
        if not entries:
            return True, None

        expected_prev = cls.GENESIS_HASH
        for idx, entry in enumerate(entries):
            # Check link to previous hash
            if entry["previous_hash"] != expected_prev:
                return False, f"Broken link at block #{idx} (Log ID: {entry.get('log_id')}): Expected prev {expected_prev}, found {entry['previous_hash']}"

            # Verify recalculated hash matches stored hash
            computed = cls.calculate_entry_hash(
                entry["previous_hash"],
                entry["timestamp"],
                entry["actor_id"],
                entry["actor_role"],
                entry["action_type"],
                entry["details"]
            )
            if computed != entry["current_hash"]:
                return False, f"Tampered record at block #{idx} (Log ID: {entry.get('log_id')}): Computed hash {computed} != Stored {entry['current_hash']}"

            expected_prev = entry["current_hash"]

        return True, None

    @classmethod
    def can_perform_action(cls, role: UserRole, action_type: str) -> bool:
        """
        Role-Based Access Control matrix for logistics and safety operations.
        """
        permissions = {
            UserRole.SYSTEM_AGENT: [
                "INGEST_TELEMETRY",
                "EVALUATE_KINETICS",
                "GENERATE_PROPOSAL",
                "RUN_SIMULATION",
                "LOG_EVENT"
            ],
            UserRole.COLD_CHAIN_OPERATOR: [
                "INGEST_TELEMETRY",
                "ADJUST_TEMPERATURE_SETPOINT",
                "VIEW_DASHBOARD",
                "LOG_EVENT"
            ],
            UserRole.LOGISTICS_COORDINATOR: [
                "INGEST_TELEMETRY",
                "DISPATCH_RETAIL_MARKDOWN",
                "REQUEST_DONATION_MATCH",
                "CONFIRM_PICKUP",
                "VIEW_DASHBOARD",
                "LOG_EVENT"
            ],
            UserRole.FOOD_SAFETY_OFFICER: [
                "INGEST_TELEMETRY",
                "EVALUATE_KINETICS",
                "APPROVE_CRITICAL_DISPATCH",
                "REJECT_UNSAFE_DISPATCH",
                "ISSUE_CONDEMNATION_ORDER",
                "OVERRIDE_AI_RECOMMENDATION",
                "VIEW_DASHBOARD",
                "LOG_EVENT"
            ],
            UserRole.ESG_AUDITOR: [
                "VIEW_DASHBOARD",
                "EXPORT_BIGQUERY_AUDIT",
                "VERIFY_LEDGER",
                "LOG_EVENT"
            ],
        }
        allowed = permissions.get(role, [])
        return action_type in allowed
