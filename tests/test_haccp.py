"""
Unit Tests for Deterministic HACCP Rules and Fail-Safe Safety Gates
"""

import unittest
from core.models import InventoryBatch, RecipientHub, FoodCategory, StorageCondition, SafetyStatus
from core.haccp_rules import HACCPRuleEngine


class TestHACCPRules(unittest.TestCase):

    def setUp(self):
        self.safe_batch = InventoryBatch(
            batch_id="TEST-B1",
            product_name="Greek Yogurt",
            category=FoodCategory.DAIRY,
            initial_qty_kg=200.0,
            current_qty_kg=200.0,
            unit_cost_usd=4.0,
            storage_condition=StorageCondition.REFRIGERATED,
            max_safe_temp_c=4.0,
            min_safe_temp_c=0.0,
            nominal_shelf_life_days=14.0,
            pack_date="2026-10-20",
            printed_expiry="2026-10-30",
            origin_facility="Test Dairy",
            current_location_name="Depot 1",
            current_lat=37.77,
            current_lon=-122.42,
            effective_rsl_hours=120.0,
            kinetic_spoilage_index=0.15,
            danger_zone_minutes=0.0,
        )

        self.cold_hub = RecipientHub(
            hub_id="HUB-COLD-1",
            name="Cold Bank",
            hub_type="FOOD_BANK",
            address="123 Road",
            lat=37.78,
            lon=-122.41,
            capacity_kg=5000.0,
            has_cold_storage=True,
            cold_storage_capacity_kg=3000.0,
            current_occupancy_kg=1000.0,
            urgency_score=0.9,
            accepted_categories=[FoodCategory.DAIRY, FoodCategory.PRODUCE],
            operating_hours="08:00 - 18:00",
            contact_phone="555-1234",
        )

        self.ambient_hub = RecipientHub(
            hub_id="HUB-DRY-2",
            name="Dry Pantry",
            hub_type="SHELTER",
            address="456 St",
            lat=37.79,
            lon=-122.40,
            capacity_kg=1000.0,
            has_cold_storage=False,
            cold_storage_capacity_kg=0.0,
            current_occupancy_kg=200.0,
            urgency_score=0.7,
            accepted_categories=[FoodCategory.DAIRY, FoodCategory.BAKERY],
            operating_hours="09:00 - 17:00",
            contact_phone="555-5678",
        )

    def test_safe_batch_with_cold_hub_passes(self):
        is_safe, requires_hitl, notes = HACCPRuleEngine.validate_allocation_plan(
            self.safe_batch, self.cold_hub, estimated_transit_min=25.0
        )
        self.assertTrue(is_safe)
        self.assertFalse(requires_hitl)

    def test_perishable_to_ambient_hub_over_threshold_fails(self):
        # Dispatching dairy to a hub without refrigeration with 60 min transit exceeds 45 min threshold
        is_safe, requires_hitl, notes = HACCPRuleEngine.validate_allocation_plan(
            self.safe_batch, self.ambient_hub, estimated_transit_min=60.0
        )
        self.assertFalse(is_safe)
        self.assertTrue(any("lacks certified refrigeration" in n for n in notes))

    def test_terminal_danger_zone_condemnation(self):
        # Batch with 250 minutes in danger zone
        self.safe_batch.danger_zone_minutes = 250.0
        is_safe, requires_hitl, notes = HACCPRuleEngine.validate_allocation_plan(
            self.safe_batch, self.cold_hub, estimated_transit_min=15.0
        )
        self.assertFalse(is_safe)
        self.assertTrue(any("exceeded 240 minutes in microbial danger zone" in n for n in notes))


if __name__ == "__main__":
    unittest.main()
