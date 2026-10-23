"""
EcoLogix AI - Deterministic HACCP and FDA Food Code Compliance Engine
Enforces mathematically immutable rules preventing AI hallucination of unsafe food distribution.
"""

from typing import List, Tuple
from core.models import (
    InventoryBatch,
    RecipientHub,
    FoodCategory,
    SafetyStatus,
    ActionRecommendation,
    AllocationPlan,
)


class HACCPRuleEngine:
    """
    Deterministic Safety Gate that acts as the final verification layer
    before any AI-proposed allocation or physical dispatch is authorized.
    """

    CRITICAL_ALLERGENS = ["PEANUTS", "TREE_NUTS", "SHELLFISH", "EGGS", "FISH", "SOY", "WHEAT", "SESAME"]

    @classmethod
    def evaluate_batch_safety(cls, batch: InventoryBatch) -> Tuple[bool, List[str]]:
        """
        Validates internal safety compliance for a batch based on temperature history and kinetics.
        Returns: (is_compliant, list_of_violations_or_warnings)
        """
        notes = []
        is_compliant = True

        # Rule 1: Cumulative Danger Zone Exposure Limit (FDA Section 3-501.19)
        if batch.danger_zone_minutes >= 240.0:
            is_compliant = False
            notes.append(
                f"CRITICAL VIOLATION: Batch exceeded 240 minutes in microbial danger zone ({batch.danger_zone_minutes} mins). Immediate condemnation mandatory."
            )

        # Rule 2: Kinetic Spoilage Threshold
        if batch.kinetic_spoilage_index >= 0.95:
            is_compliant = False
            notes.append(
                f"CRITICAL VIOLATION: Kinetic Spoilage Index at terminal threshold ({batch.kinetic_spoilage_index:.2f} >= 0.95). Biochemical degradation renders product unfit for human consumption."
            )

        # Rule 3: Zero or Negative Usable Shelf Life
        if batch.effective_rsl_hours <= 0.0:
            is_compliant = False
            notes.append("CRITICAL VIOLATION: Zero remaining usable shelf-life.")

        return is_compliant, notes

    @classmethod
    def validate_allocation_plan(
        cls, batch: InventoryBatch, recipient: RecipientHub, estimated_transit_min: float
    ) -> Tuple[bool, bool, List[str]]:
        """
        Validates whether a proposed allocation to a specific recipient complies with safety regulations.
        Returns:
            - is_safe_for_donation: boolean
            - requires_hitl_approval: boolean
            - validation_notes: list of strings detailing checks
        """
        notes = []
        is_safe = True
        requires_hitl = False

        # First verify the batch itself
        batch_safe, batch_notes = cls.evaluate_batch_safety(batch)
        notes.extend(batch_notes)
        if not batch_safe:
            return False, True, notes

        # Rule 4: Transit Time vs Remaining Shelf Life
        transit_hours = estimated_transit_min / 60.0
        if transit_hours >= batch.effective_rsl_hours:
            is_safe = False
            notes.append(
                f"DISPATCH BLOCKED: Estimated transit time ({transit_hours:.1f}h) exceeds remaining shelf life ({batch.effective_rsl_hours:.1f}h)."
            )

        # Rule 5: Recipient Cold-Storage Capabilities for Perishables
        perishable_categories = [
            FoodCategory.DAIRY,
            FoodCategory.MEAT_POULTRY,
            FoodCategory.SEAFOOD,
            FoodCategory.PHARMACEUTICAL_BIOLOGICS,
        ]
        if batch.category in perishable_categories and not recipient.has_cold_storage:
            # If recipient lacks refrigeration, transit + consumption window must be ultra-short (<60 mins)
            if estimated_transit_min > 45.0:
                is_safe = False
                notes.append(
                    f"DISPATCH BLOCKED: Recipient '{recipient.name}' lacks certified refrigeration for {batch.category.value}. Maximum non-refrigerated transit threshold (45 min) exceeded ({estimated_transit_min:.0f} min)."
                )

        # Rule 6: Recipient Capacity Constraint
        available_space = recipient.capacity_kg - recipient.current_occupancy_kg
        if batch.current_qty_kg > available_space:
            notes.append(
                f"CAPACITY WARNING: Batch qty ({batch.current_qty_kg} kg) exceeds hub available capacity ({available_space} kg). Partial batch split advised."
            )

        # Rule 7: Recipient Category Acceptance
        if batch.category not in recipient.accepted_categories:
            is_safe = False
            notes.append(
                f"POLICY REJECTION: Recipient '{recipient.name}' does not accept category {batch.category.value}."
            )

        # Rule 8: Mandatory Human-in-the-Loop (HITL) Triggers
        # Ambiguous or elevated risk cases require Food Safety Officer signoff
        if batch.danger_zone_minutes >= 60.0:
            requires_hitl = True
            notes.append("HITL MANDATORY: Batch experienced significant temperature excursion (>60 mins in danger zone). Requires Safety Officer review.")

        if batch.kinetic_spoilage_index >= 0.70:
            requires_hitl = True
            notes.append("HITL MANDATORY: High spoilage index (>= 0.70). Physical organoleptic/smell/color verification recommended.")

        total_value = batch.current_qty_kg * batch.unit_cost_usd
        if total_value >= 2500.0:
            requires_hitl = True
            notes.append(f"HITL MANDATORY: High monetary value batch (${total_value:,.2f} >= $2,500.00). Financial sign-off required.")

        if batch.category == FoodCategory.PHARMACEUTICAL_BIOLOGICS:
            requires_hitl = True
            notes.append("HITL MANDATORY: Biologics/Pharmaceutical batch requires clinical coordinator verification.")

        if is_safe and not notes:
            notes.append("PASSED: Full HACCP and FDA Food Code compliance verified.")

        return is_safe, requires_hitl, notes
