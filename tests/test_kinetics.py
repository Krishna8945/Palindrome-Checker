"""
Unit Tests for Spoilage Kinetics & Arrhenius Degradation Engine
"""

import unittest
from core.models import FoodCategory, SafetyStatus, IoTTelemetry
from core.kinetics import KineticsEngine


class TestKineticsEngine(unittest.TestCase):

    def test_q10_multiplier(self):
        # Dairy Q10 is 2.8. At 14°C vs 4°C ref (+10°C), multiplier should be exactly 2.8
        mult = KineticsEngine.calculate_spoilage_rate_multiplier(
            current_temp_c=14.0, ref_temp_c=4.0, category=FoodCategory.DAIRY
        )
        self.assertAlmostEqual(mult, 2.8, places=2)

    def test_danger_zone_accumulation(self):
        # 16 readings at 15-minute intervals in Danger Zone (12°C) = 240 minutes
        telemetry = [
            IoTTelemetry(temperature_c=12.0, humidity_pct=80.0, location_lat=37.7, location_lon=-122.4)
            for _ in range(16)
        ]
        ksi, rsl, danger_mins, status = KineticsEngine.evaluate_telemetry_stream(
            telemetry=telemetry,
            category=FoodCategory.MEAT_POULTRY,
            nominal_shelf_life_days=5.0,
            ref_temp_c=4.0,
            default_interval_minutes=15.0,
        )
        self.assertEqual(danger_mins, 240.0)
        # Under FDA Food Code, >=240 mins must be classified as HAZARDOUS_UNSAFE
        self.assertEqual(status, SafetyStatus.HAZARDOUS_UNSAFE)

    def test_optimal_storage(self):
        # Steady 2.0°C below reference 4.0°C
        telemetry = [
            IoTTelemetry(temperature_c=2.0, humidity_pct=85.0, location_lat=37.7, location_lon=-122.4)
            for _ in range(5)
        ]
        ksi, rsl, danger_mins, status = KineticsEngine.evaluate_telemetry_stream(
            telemetry=telemetry,
            category=FoodCategory.DAIRY,
            nominal_shelf_life_days=10.0,
            ref_temp_c=4.0,
            default_interval_minutes=15.0,
        )
        self.assertEqual(danger_mins, 0.0)
        self.assertLess(ksi, 0.1)
        self.assertEqual(status, SafetyStatus.OPTIMAL)


if __name__ == "__main__":
    unittest.main()
