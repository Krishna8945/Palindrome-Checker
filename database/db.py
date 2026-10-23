"""
EcoLogix AI - Database and Simulation Seed Data Store
Provides persistent state and realistic cold-chain inventory datasets,
IoT sensor streams, and recipient hubs.
"""

import copy
import datetime
from typing import List, Dict, Optional
from core.models import (
    InventoryBatch,
    RecipientHub,
    FoodCategory,
    StorageCondition,
    SafetyStatus,
    IoTTelemetry,
)
from core.kinetics import KineticsEngine


class DataStore:
    """
    In-memory and transactional state manager for cold chain batches and facilities.
    """

    def __init__(self):
        self.batches: Dict[str, InventoryBatch] = {}
        self.recipient_hubs: Dict[str, RecipientHub] = {}
        self.initialize_seed_data()

    def initialize_seed_data(self):
        """
        Seeds diverse real-world cold-chain inventory scenarios.
        """
        self.batches.clear()
        self.recipient_hubs.clear()

        # Recipient Hubs
        hubs = [
            RecipientHub(
                hub_id="hub-fb-01",
                name="Metro Hope Harvest Food Bank",
                hub_type="FOOD_BANK",
                address="450 Logistics Blvd, Sector 7",
                lat=37.7749,
                lon=-122.4194,
                capacity_kg=15000.0,
                has_cold_storage=True,
                cold_storage_capacity_kg=8000.0,
                current_occupancy_kg=5200.0,
                urgency_score=0.95,
                accepted_categories=[
                    FoodCategory.DAIRY,
                    FoodCategory.PRODUCE,
                    FoodCategory.MEAT_POULTRY,
                    FoodCategory.SEAFOOD,
                    FoodCategory.PREPARED_MEALS,
                    FoodCategory.BAKERY,
                ],
                operating_hours="06:00 - 22:00",
                contact_phone="+1-555-0199",
            ),
            RecipientHub(
                hub_id="hub-sh-02",
                name="St. Jude Community Shelter & Kitchen",
                hub_type="COMMUNITY_KITCHEN",
                address="128 Mission Ave",
                lat=37.7833,
                lon=-122.4167,
                capacity_kg=2500.0,
                has_cold_storage=True,
                cold_storage_capacity_kg=1200.0,
                current_occupancy_kg=1100.0,
                urgency_score=0.88,
                accepted_categories=[
                    FoodCategory.PRODUCE,
                    FoodCategory.DAIRY,
                    FoodCategory.PREPARED_MEALS,
                    FoodCategory.BAKERY,
                ],
                operating_hours="08:00 - 20:00",
                contact_phone="+1-555-0142",
            ),
            RecipientHub(
                hub_id="hub-bio-03",
                name="GreenVolt Biomethane & Anaerobic Digestion Plant",
                hub_type="BIOGAS_DIGESTER",
                address="880 Industrial Way",
                lat=37.7312,
                lon=-122.3850,
                capacity_kg=60000.0,
                has_cold_storage=False,
                cold_storage_capacity_kg=0.0,
                current_occupancy_kg=12000.0,
                urgency_score=0.40,
                accepted_categories=[
                    FoodCategory.DAIRY,
                    FoodCategory.PRODUCE,
                    FoodCategory.MEAT_POULTRY,
                    FoodCategory.SEAFOOD,
                    FoodCategory.PREPARED_MEALS,
                    FoodCategory.BAKERY,
                ],
                operating_hours="24/7 Operations",
                contact_phone="+1-555-0188",
            ),
            RecipientHub(
                hub_id="hub-pantry-04",
                name="Harbor Neighborhood Emergency Pantry",
                hub_type="SHELTER",
                address="92 Pier Side Road",
                lat=37.7950,
                lon=-122.3990,
                capacity_kg=900.0,
                has_cold_storage=False,
                cold_storage_capacity_kg=0.0,
                current_occupancy_kg=350.0,
                urgency_score=0.75,
                accepted_categories=[
                    FoodCategory.PRODUCE,
                    FoodCategory.BAKERY,
                ],
                operating_hours="09:00 - 18:00",
                contact_phone="+1-555-0177",
            ),
        ]
        for hub in hubs:
            self.recipient_hubs[hub.hub_id] = hub

        # Inventory Batches
        now = datetime.datetime.now(datetime.timezone.utc)
        yesterday = (now - datetime.timedelta(days=1)).isoformat()
        future_5d = (now + datetime.timedelta(days=5)).isoformat()
        future_2d = (now + datetime.timedelta(days=2)).isoformat()
        future_1d = (now + datetime.timedelta(hours=18)).isoformat()

        # Batch 1: Dairy (Optimal)
        b1_telemetry = [
            IoTTelemetry(temperature_c=2.5, humidity_pct=85.0, location_lat=37.7700, location_lon=-122.4200),
            IoTTelemetry(temperature_c=2.8, humidity_pct=84.0, location_lat=37.7710, location_lon=-122.4210),
            IoTTelemetry(temperature_c=3.1, humidity_pct=83.0, location_lat=37.7725, location_lon=-122.4215),
        ]
        b1 = InventoryBatch(
            batch_id="BATCH-DAIRY-101",
            product_name="Organic Pasture Whole Milk (1 Gallon)",
            category=FoodCategory.DAIRY,
            initial_qty_kg=1200.0,
            current_qty_kg=1200.0,
            unit_cost_usd=3.50,
            storage_condition=StorageCondition.REFRIGERATED,
            max_safe_temp_c=4.0,
            min_safe_temp_c=0.0,
            nominal_shelf_life_days=10.0,
            pack_date=yesterday,
            printed_expiry=future_5d,
            origin_facility="Valley Green Organic Dairy Farm",
            current_location_name="Reefer Transport Truck #402 (In Transit)",
            current_lat=37.7725,
            current_lon=-122.4215,
            allergens=["MILK"],
            telemetry_history=b1_telemetry,
        )

        # Batch 2: Seafood (Temperature excursion, salvageable emergency match)
        b2_telemetry = [
            IoTTelemetry(temperature_c=2.0, humidity_pct=90.0, location_lat=37.7600, location_lon=-122.4100),
            IoTTelemetry(temperature_c=6.5, humidity_pct=88.0, location_lat=37.7620, location_lon=-122.4120),
            IoTTelemetry(temperature_c=7.8, humidity_pct=86.0, location_lat=37.7640, location_lon=-122.4135),
            IoTTelemetry(temperature_c=6.9, humidity_pct=85.0, location_lat=37.7650, location_lon=-122.4140),
        ]
        b2 = InventoryBatch(
            batch_id="BATCH-FISH-202",
            product_name="Wild Pacific Sockeye Salmon Fillets",
            category=FoodCategory.SEAFOOD,
            initial_qty_kg=480.0,
            current_qty_kg=480.0,
            unit_cost_usd=18.50,
            storage_condition=StorageCondition.REFRIGERATED,
            max_safe_temp_c=3.0,
            min_safe_temp_c=-1.0,
            nominal_shelf_life_days=4.0,
            pack_date=yesterday,
            printed_expiry=future_2d,
            origin_facility="Pacific Catch Processing Dock 4",
            current_location_name="Cross-Dock Distribution Depot West",
            current_lat=37.7650,
            current_lon=-122.4140,
            allergens=["FISH"],
            telemetry_history=b2_telemetry,
        )

        # Batch 3: Meat/Poultry (Critical Breach: Exceeded 240 mins Danger Zone -> Must Condemn to Biogas)
        b3_telemetry = [
            IoTTelemetry(temperature_c=3.0, humidity_pct=80.0, location_lat=37.7400, location_lon=-122.3900),
            IoTTelemetry(temperature_c=12.5, humidity_pct=72.0, location_lat=37.7420, location_lon=-122.3920),
            IoTTelemetry(temperature_c=14.8, humidity_pct=68.0, location_lat=37.7450, location_lon=-122.3950),
            IoTTelemetry(temperature_c=16.2, humidity_pct=65.0, location_lat=37.7470, location_lon=-122.3970),
        ]
        b3 = InventoryBatch(
            batch_id="BATCH-POULTRY-303",
            product_name="Fresh Boneless Chicken Breast Cutlets",
            category=FoodCategory.MEAT_POULTRY,
            initial_qty_kg=920.0,
            current_qty_kg=920.0,
            unit_cost_usd=7.20,
            storage_condition=StorageCondition.REFRIGERATED,
            max_safe_temp_c=4.0,
            min_safe_temp_c=0.0,
            nominal_shelf_life_days=5.0,
            pack_date=yesterday,
            printed_expiry=future_2d,
            origin_facility="Golden Ridge Poultry Processing Plant",
            current_location_name="Regional Hub Cold Vault 3B",
            current_lat=37.7470,
            current_lon=-122.3970,
            allergens=[],
            telemetry_history=b3_telemetry,
        )

        # Batch 4: Produce (Fresh, near-date, perfect for dynamic retail markdown)
        b4_telemetry = [
            IoTTelemetry(temperature_c=3.8, humidity_pct=92.0, location_lat=37.7850, location_lon=-122.4080),
            IoTTelemetry(temperature_c=4.1, humidity_pct=91.0, location_lat=37.7860, location_lon=-122.4090),
        ]
        b4 = InventoryBatch(
            batch_id="BATCH-PRODUCE-404",
            product_name="Organic Crisp Romaine Hearts (3-pk)",
            category=FoodCategory.PRODUCE,
            initial_qty_kg=650.0,
            current_qty_kg=650.0,
            unit_cost_usd=2.80,
            storage_condition=StorageCondition.REFRIGERATED,
            max_safe_temp_c=5.0,
            min_safe_temp_c=1.0,
            nominal_shelf_life_days=7.0,
            pack_date=yesterday,
            printed_expiry=future_1d,
            origin_facility="Salinas Valley Produce Co-op",
            current_location_name="Urban Supermarket Store #18",
            current_lat=37.7860,
            current_lon=-122.4090,
            allergens=[],
            telemetry_history=b4_telemetry,
        )

        # Batch 5: Pharmaceutical Biologics (Pediatric Insulin, high financial value, triggers HITL)
        b5_telemetry = [
            IoTTelemetry(temperature_c=4.2, humidity_pct=50.0, location_lat=37.7550, location_lon=-122.4300),
            IoTTelemetry(temperature_c=5.5, humidity_pct=49.0, location_lat=37.7560, location_lon=-122.4310),
            IoTTelemetry(temperature_c=4.8, humidity_pct=51.0, location_lat=37.7570, location_lon=-122.4320),
        ]
        b5 = InventoryBatch(
            batch_id="BATCH-PHARMA-505",
            product_name="Pediatric Recombinant Human Insulin Glargine",
            category=FoodCategory.PHARMACEUTICAL_BIOLOGICS,
            initial_qty_kg=45.0,
            current_qty_kg=45.0,
            unit_cost_usd=850.00,  # $38,250 batch value!
            storage_condition=StorageCondition.REFRIGERATED,
            max_safe_temp_c=6.0,
            min_safe_temp_c=2.0,
            nominal_shelf_life_days=28.0,
            pack_date=yesterday,
            printed_expiry=future_5d,
            origin_facility="BioHealth Biologics Manufacturing Lab",
            current_location_name="BioCold Secure Courier Van #12",
            current_lat=37.7570,
            current_lon=-122.4320,
            allergens=[],
            telemetry_history=b5_telemetry,
        )

        # Register and pre-calculate kinetics for all initial batches
        for b in [b1, b2, b3, b4, b5]:
            # Simulate historical danger zone minutes for batch 3 to demonstrate FDA breach
            if b.batch_id == "BATCH-POULTRY-303":
                b.danger_zone_minutes = 255.0  # Trigger 4-hour FDA breach!
                b.kinetic_spoilage_index = 0.96
                b.effective_rsl_hours = 0.0
                b.safety_status = SafetyStatus.HAZARDOUS_UNSAFE
            else:
                ksi, rsl, danger_mins, status = KineticsEngine.evaluate_telemetry_stream(
                    telemetry=b.telemetry_history,
                    category=b.category,
                    nominal_shelf_life_days=b.nominal_shelf_life_days,
                )
                b.kinetic_spoilage_index = ksi
                b.effective_rsl_hours = rsl
                b.danger_zone_minutes = danger_mins
                b.safety_status = status

            self.batches[b.batch_id] = b

    def get_all_batches(self) -> List[InventoryBatch]:
        return list(self.batches.values())

    def get_batch(self, batch_id: str) -> Optional[InventoryBatch]:
        return self.batches.get(batch_id)

    def get_all_hubs(self) -> List[RecipientHub]:
        return list(self.recipient_hubs.values())

    def get_hub(self, hub_id: str) -> Optional[RecipientHub]:
        return self.recipient_hubs.get(hub_id)

    def simulate_telemetry_tick(
        self, batch_id: str, temp_delta_c: float, duration_min: float = 15.0
    ) -> Optional[InventoryBatch]:
        """
        Simulates an IoT sensor event (e.g. cooling compressor breakdown or cooling restoration).
        """
        batch = self.batches.get(batch_id)
        if not batch:
            return None

        last_reading = batch.telemetry_history[-1] if batch.telemetry_history else IoTTelemetry(
            temperature_c=4.0, humidity_pct=80.0, location_lat=batch.current_lat, location_lon=batch.current_lon
        )
        new_temp = round(last_reading.temperature_c + temp_delta_c, 1)

        new_reading = IoTTelemetry(
            temperature_c=new_temp,
            humidity_pct=last_reading.humidity_pct,
            location_lat=batch.current_lat,
            location_lon=batch.current_lon,
            door_open_duration_sec=30 if temp_delta_c > 2.0 else 0,
        )
        batch.telemetry_history.append(new_reading)

        # Recalculate kinetics
        ksi, rsl, danger_mins, status = KineticsEngine.evaluate_telemetry_stream(
            telemetry=batch.telemetry_history,
            category=batch.category,
            nominal_shelf_life_days=batch.nominal_shelf_life_days,
            default_interval_minutes=duration_min,
        )
        batch.kinetic_spoilage_index = ksi
        batch.effective_rsl_hours = rsl
        batch.danger_zone_minutes = danger_mins
        batch.safety_status = status

        return batch


# Global singleton database instance
db_instance = DataStore()
