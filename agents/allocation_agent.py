"""
EcoLogix AI - Logistics & Multi-Criteria Allocation Agent
Optimizes perishable redistribution between supply sources and demand hubs
considering transit latency, cold capacity, urgency scores, and ESG impact.
"""

import math
from typing import List, Optional, Tuple, Dict, Any
from core.models import (
    InventoryBatch,
    RecipientHub,
    AllocationPlan,
    ActionRecommendation,
    FoodCategory,
)


class AllocationAgent:
    """
    Autonomous logistics agent solving multi-objective distribution matching.
    """

    def __init__(self, agent_id: str = "agent-logistics-optimizer"):
        self.agent_id = agent_id

    @staticmethod
    def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculates great-circle distance between two GPS coordinates in kilometers.
        """
        r = 6371.0  # Earth's radius in km
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = math.sin(delta_phi / 2.0) ** 2 + \
            math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return round(r * c, 2)

    @classmethod
    def estimate_transit_time_min(cls, distance_km: float, is_urban: bool = True) -> float:
        """
        Estimates commercial refrigerated transport transit time including buffer.
        """
        avg_speed_kmh = 35.0 if is_urban else 65.0
        loading_unloading_buffer_min = 20.0
        travel_time_min = (distance_km / avg_speed_kmh) * 60.0
        return round(travel_time_min + loading_unloading_buffer_min, 1)

    def find_optimal_allocation(
        self,
        batch: InventoryBatch,
        candidate_hubs: List[RecipientHub],
        triage_recommendation: ActionRecommendation,
    ) -> Optional[Tuple[RecipientHub, float, float, float]]:
        """
        Finds the highest-scoring recipient hub for the batch based on the triage recommendation.
        Returns: (best_hub, distance_km, transit_time_min, match_score)
        """
        is_biogas_destination = triage_recommendation in [
            ActionRecommendation.ANAEROBIC_DIGESTION_BIOGAS,
            ActionRecommendation.BIOHAZARD_DISPOSAL,
        ]

        scored_candidates = []

        for hub in candidate_hubs:
            # Check hub type compatibility
            if is_biogas_destination:
                if hub.hub_type not in ["BIOGAS_DIGESTER", "COMPOSTING_FACILITY"]:
                    continue
            else:
                if hub.hub_type in ["BIOGAS_DIGESTER", "COMPOSTING_FACILITY"]:
                    continue

            # Check capacity
            available_space = hub.capacity_kg - hub.current_occupancy_kg
            if available_space < (batch.current_qty_kg * 0.3):  # Must accept at least 30% of batch
                continue

            # Distance & transit time
            dist_km = self.haversine_distance_km(
                batch.current_lat, batch.current_lon, hub.lat, hub.lon
            )
            transit_min = self.estimate_transit_time_min(dist_km)

            # If perishable and hub lacks cold storage, penalize severely or skip if transit > 45 mins
            perishable_cats = [FoodCategory.DAIRY, FoodCategory.MEAT_POULTRY, FoodCategory.SEAFOOD]
            if batch.category in perishable_cats and not hub.has_cold_storage:
                if transit_min > 45.0:
                    continue

            # Multi-objective score:
            # - High urgency score (+40 pts)
            # - Low distance / transit time (+30 pts)
            # - Cold storage matching (+20 pts)
            # - High available capacity (+10 pts)
            dist_score = max(0.0, 1.0 - (dist_km / 100.0)) * 30.0
            urgency_score = hub.urgency_score * 40.0
            cold_score = 20.0 if (hub.has_cold_storage or batch.category not in perishable_cats) else 0.0
            capacity_score = min(10.0, (available_space / max(1.0, batch.current_qty_kg)) * 10.0)

            total_score = dist_score + urgency_score + cold_score + capacity_score
            scored_candidates.append((hub, dist_km, transit_min, total_score))

        if not scored_candidates:
            return None

        # Sort descending by match score
        scored_candidates.sort(key=lambda x: x[3], reverse=True)
        return scored_candidates[0]

    def create_allocation_plan(
        self,
        batch: InventoryBatch,
        selected_hub: RecipientHub,
        distance_km: float,
        transit_time_min: float,
        recommended_action: ActionRecommendation,
        ai_reasoning: str,
    ) -> AllocationPlan:
        """
        Constructs a complete AllocationPlan with ESG analytics (CO2e, meals, water, financial recovery).
        """
        qty = batch.current_qty_kg
        
        # Environmental and Social Impact Metrics (EPA WARM standard)
        if recommended_action in [
            ActionRecommendation.EMERGENCY_FOOD_BANK_DISPATCH,
            ActionRecommendation.SECONDARY_PROCESSING_KITCHEN,
            ActionRecommendation.RAPID_RETAIL_MARKDOWN,
        ]:
            co2e_saved = round(qty * 1.9, 1)  # 1.9 kg CO2e prevented per kg diverted from landfill
            meals = int(qty / 0.45)           # ~450g per standard meal
            financial_saved = round(qty * batch.unit_cost_usd, 2)
        elif recommended_action == ActionRecommendation.ANAEROBIC_DIGESTION_BIOGAS:
            co2e_saved = round(qty * 0.85, 1)  # Biogas recovery offset
            meals = 0
            financial_saved = round(qty * 0.15, 2)  # Renewable feedstock byproduct value
        else:
            co2e_saved = 0.0
            meals = 0
            financial_saved = 0.0

        plan = AllocationPlan(
            plan_id=f"plan-{batch.batch_id}-{selected_hub.hub_id}",
            batch_id=batch.batch_id,
            batch_product=batch.product_name,
            batch_category=batch.category,
            quantity_kg=qty,
            source_location=batch.current_location_name,
            recipient_id=selected_hub.hub_id,
            recipient_name=selected_hub.name,
            recipient_type=selected_hub.hub_type,
            distance_km=distance_km,
            estimated_transit_time_min=transit_time_min,
            cold_chain_maintained_in_transit=True,
            recommended_action=recommended_action,
            ai_reasoning=ai_reasoning,
            co2e_abated_kg=co2e_saved,
            meals_provided=meals,
            economic_value_saved_usd=financial_saved,
            haccp_compliant=False,  # Must be verified by Safety Gate Agent
            haccp_validation_notes=[],
            hitl_required=False,
            hitl_approved=False,
        )
        return plan
