"""
EcoLogix AI - Deterministic Safety Gate Agent
Acts as an unbreachable safeguard validating all AI allocation proposals
against HACCP food safety standards and microbiological danger zone rules.
"""

from typing import Tuple, List
from core.models import InventoryBatch, RecipientHub, AllocationPlan, ActionRecommendation
from core.haccp_rules import HACCPRuleEngine


class SafetyGateAgent:
    """
    Deterministic verification agent that enforces zero-tolerance food safety.
    """

    def __init__(self, agent_id: str = "agent-safety-gate"):
        self.agent_id = agent_id

    def inspect_and_certify_plan(
        self,
        batch: InventoryBatch,
        recipient: RecipientHub,
        plan: AllocationPlan
    ) -> Tuple[AllocationPlan, bool]:
        """
        Conducts deterministic verification on the allocation plan.
        If unsafe, mutates the plan to blocked status and overrides action.
        Returns: (certified_plan, passed_verification)
        """
        is_safe, requires_hitl, notes = HACCPRuleEngine.validate_allocation_plan(
            batch=batch,
            recipient=recipient,
            estimated_transit_min=plan.estimated_transit_time_min
        )

        plan.haccp_compliant = is_safe
        plan.haccp_validation_notes = notes
        plan.hitl_required = plan.hitl_required or requires_hitl

        if not is_safe:
            # Plan failed critical safety gate - Override action recommendation!
            if batch.danger_zone_minutes >= 240.0 or batch.kinetic_spoilage_index >= 0.95:
                plan.recommended_action = ActionRecommendation.ANAEROBIC_DIGESTION_BIOGAS
                plan.ai_reasoning += " [SAFETY GATE OVERRIDE: Microbiological danger threshold exceeded. Distribution for human consumption strictly blocked by deterministic HACCP gate.]"
                plan.meals_provided = 0
                plan.co2e_abated_kg = round(plan.quantity_kg * 0.85, 1)

        return plan, is_safe
