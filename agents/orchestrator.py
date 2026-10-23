"""
EcoLogix AI - Multi-Agent Supervisor & Orchestrator
Coordinates the continuous agentic lifecycle:
Telemetry -> Kinetics -> Gemini Triage -> Logistics Allocation -> HACCP Safety Gate -> Cryptographic Ledger.
"""

import time
import hashlib
import datetime
from typing import List, Dict, Any, Optional, Tuple
from core.models import (
    InventoryBatch,
    RecipientHub,
    AllocationPlan,
    IoTTelemetry,
    UserRole,
    AuditLogEntry,
    ActionRecommendation,
    SafetyStatus,
)
from core.gemini_client import GeminiClient
from core.security import SecurityEngine
from agents.telemetry_agent import TelemetryAgent
from agents.triage_agent import TriageAgent
from agents.allocation_agent import AllocationAgent
from agents.safety_gate_agent import SafetyGateAgent


class MultiAgentOrchestrator:
    """
    Supervisor coordinating autonomous agents with strict safety boundaries and human-in-the-loop controls.
    """

    def __init__(self, gemini_client: Optional[GeminiClient] = None):
        self.gemini_client = gemini_client or GeminiClient()
        self.telemetry_agent = TelemetryAgent()
        self.triage_agent = TriageAgent(self.gemini_client)
        self.allocation_agent = AllocationAgent()
        self.safety_gate_agent = SafetyGateAgent()

        # In-memory session stores for runtime state
        self.audit_ledger: List[Dict[str, Any]] = []
        self.active_plans: Dict[str, AllocationPlan] = {}
        self.pending_hitl_plans: Dict[str, AllocationPlan] = {}

    def get_latest_hash(self) -> str:
        if not self.audit_ledger:
            return SecurityEngine.GENESIS_HASH
        return self.audit_ledger[-1]["current_hash"]

    def record_audit_log(
        self,
        actor_id: str,
        actor_role: UserRole,
        action_type: str,
        batch_id: Optional[str],
        details: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Creates a tamper-evident SHA-256 chained audit block.
        """
        prev_hash = self.get_latest_hash()
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        current_hash = SecurityEngine.calculate_entry_hash(
            previous_hash=prev_hash,
            timestamp=timestamp,
            actor_id=actor_id,
            actor_role=actor_role.value,
            action_type=action_type,
            details=details,
        )

        entry = {
            "log_id": f"log-{len(self.audit_ledger) + 1:05d}",
            "timestamp": timestamp,
            "actor_id": actor_id,
            "actor_role": actor_role.value,
            "action_type": action_type,
            "batch_id": batch_id,
            "details": details,
            "previous_hash": prev_hash,
            "current_hash": current_hash,
        }
        self.audit_ledger.append(entry)
        return entry

    def run_pipeline_for_batch(
        self,
        batch: InventoryBatch,
        candidate_hubs: List[RecipientHub],
        new_reading: Optional[IoTTelemetry] = None,
    ) -> Dict[str, Any]:
        """
        Executes the end-to-end multi-agent pipeline for a perishable batch.
        Returns detailed trace of all agent thoughts, decisions, latencies, and final plan.
        """
        trace: Dict[str, Any] = {
            "batch_id": batch.batch_id,
            "product": batch.product_name,
            "pipeline_start": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "stages": [],
        }

        # Stage 1: Sensing & Kinetics Recalculation
        stage1_start = time.time()
        if new_reading:
            batch, alert = self.telemetry_agent.process_new_reading(batch, new_reading)
        else:
            # Re-evaluate with current history
            pass

        stage1_ms = (time.time() - stage1_start) * 1000
        trace["stages"].append({
            "stage_name": "SENSING_AND_KINETICS",
            "agent": self.telemetry_agent.agent_id,
            "latency_ms": round(stage1_ms, 2),
            "output": {
                "kinetic_spoilage_index": batch.kinetic_spoilage_index,
                "effective_rsl_hours": batch.effective_rsl_hours,
                "danger_zone_minutes": batch.danger_zone_minutes,
                "safety_status": batch.safety_status.value,
            },
        })

        # Stage 2: Gemini Cognitive Triage & Risk Reasoning
        stage2_start = time.time()
        triage_data, stage2_ms, engine_name = self.triage_agent.evaluate_batch(batch)
        verdict_str = triage_data.get("triage_verdict", ActionRecommendation.MAINTAIN_MONITORING.value)
        try:
            recommended_action = ActionRecommendation(verdict_str)
        except ValueError:
            recommended_action = ActionRecommendation.MAINTAIN_MONITORING

        trace["stages"].append({
            "stage_name": "COGNITIVE_TRIAGE",
            "agent": self.triage_agent.agent_id,
            "engine": engine_name,
            "latency_ms": round(stage2_ms, 2),
            "output": triage_data,
        })

        # Stage 3: Logistics & Geospatial Allocation Matching
        stage3_start = time.time()
        allocation_match = self.allocation_agent.find_optimal_allocation(
            batch=batch,
            candidate_hubs=candidate_hubs,
            triage_recommendation=recommended_action,
        )

        plan = None
        if allocation_match:
            best_hub, dist_km, transit_min, score = allocation_match
            plan = self.allocation_agent.create_allocation_plan(
                batch=batch,
                selected_hub=best_hub,
                distance_km=dist_km,
                transit_time_min=transit_min,
                recommended_action=recommended_action,
                ai_reasoning=triage_data.get("risk_assessment", ""),
            )
            plan.hitl_required = triage_data.get("hitl_required", False)

        stage3_ms = (time.time() - stage3_start) * 1000
        trace["stages"].append({
            "stage_name": "LOGISTICS_ALLOCATION",
            "agent": self.allocation_agent.agent_id,
            "latency_ms": round(stage3_ms, 2),
            "output": {
                "matched_hub": plan.recipient_name if plan else "None",
                "distance_km": plan.distance_km if plan else 0.0,
                "estimated_transit_min": plan.estimated_transit_time_min if plan else 0.0,
                "co2e_abated_kg": plan.co2e_abated_kg if plan else 0.0,
                "meals_provided": plan.meals_provided if plan else 0,
            },
        })

        # Stage 4: Deterministic HACCP Safety Gate
        stage4_start = time.time()
        if plan and allocation_match:
            plan, passed_gate = self.safety_gate_agent.inspect_and_certify_plan(
                batch=batch,
                recipient=best_hub,
                plan=plan,
            )
        else:
            passed_gate = True

        stage4_ms = (time.time() - stage4_start) * 1000
        trace["stages"].append({
            "stage_name": "HACCP_SAFETY_GATE",
            "agent": self.safety_gate_agent.agent_id,
            "latency_ms": round(stage4_ms, 2),
            "output": {
                "haccp_compliant": plan.haccp_compliant if plan else True,
                "hitl_required": plan.hitl_required if plan else False,
                "validation_notes": plan.haccp_validation_notes if plan else [],
            },
        })

        # Stage 5: Execution or HITL Escalation & Cryptographic Ledger Logging
        if plan:
            # Generate cryptographic verification dispatch token
            secret_basis = f"{plan.plan_id}:{plan.batch_id}:{plan.recipient_id}:{plan.quantity_kg}:{plan.created_at}"
            plan.verification_hash = hashlib.sha256(secret_basis.encode()).hexdigest()[:16].upper()

            self.active_plans[plan.plan_id] = plan
            if plan.hitl_required and not plan.hitl_approved:
                self.pending_hitl_plans[plan.plan_id] = plan

            # Record in SHA-256 chained audit ledger
            self.record_audit_log(
                actor_id="MULTI_AGENT_SUPERVISOR",
                actor_role=UserRole.SYSTEM_AGENT,
                action_type="ALLOCATION_PLAN_GENERATED",
                batch_id=batch.batch_id,
                details={
                    "plan_id": plan.plan_id,
                    "recipient": plan.recipient_name,
                    "action": plan.recommended_action.value,
                    "haccp_compliant": plan.haccp_compliant,
                    "hitl_required": plan.hitl_required,
                    "meals": plan.meals_provided,
                    "co2e_kg": plan.co2e_abated_kg,
                    "verification_hash": plan.verification_hash,
                },
            )

        total_latency = stage1_ms + stage2_ms + stage3_ms + stage4_ms
        trace["total_latency_ms"] = round(total_latency, 2)
        trace["final_plan"] = plan.model_dump() if plan else None

        return trace

    def approve_hitl_plan(
        self, plan_id: str, approver_name: str, approver_role: UserRole
    ) -> Tuple[bool, Optional[AllocationPlan], str]:
        """
        Human-in-the-Loop decision gateway: Food Safety Officer signs off on high-risk salvage plan.
        """
        if not SecurityEngine.can_perform_action(approver_role, "APPROVE_CRITICAL_DISPATCH"):
            return False, None, f"Permission Denied: Role {approver_role.value} cannot approve critical dispatch."

        plan = self.pending_hitl_plans.get(plan_id) or self.active_plans.get(plan_id)
        if not plan:
            return False, None, "Plan not found."

        plan.hitl_approved = True
        plan.hitl_approved_by = approver_name

        if plan_id in self.pending_hitl_plans:
            del self.pending_hitl_plans[plan_id]

        # Audit log the human override/approval
        self.record_audit_log(
            actor_id=approver_name,
            actor_role=approver_role,
            action_type="HITL_DISPATCH_APPROVED",
            batch_id=plan.batch_id,
            details={
                "plan_id": plan.plan_id,
                "approved_by": approver_name,
                "role": approver_role.value,
                "verification_hash": plan.verification_hash,
            },
        )

        return True, plan, "Successfully approved and certified by Safety Officer."
