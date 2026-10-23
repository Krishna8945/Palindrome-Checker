"""
EcoLogix AI - Food Science & Spoilage Kinetics Engine
Implements Arrhenius Biochemical Decay, Q-10 Temperature Coefficient,
and FDA Time/Temperature Control for Safety (TCS) calculations.
"""

import math
from typing import List, Tuple
from core.models import FoodCategory, StorageCondition, SafetyStatus, IoTTelemetry


# Q10 degradation coefficients by food category
# Q10 represents the factor by which degradation velocity multiplies with a 10°C rise
Q10_FACTORS = {
    FoodCategory.DAIRY: 2.8,
    FoodCategory.PRODUCE: 2.2,
    FoodCategory.MEAT_POULTRY: 3.2,
    FoodCategory.SEAFOOD: 3.5,
    FoodCategory.PREPARED_MEALS: 2.7,
    FoodCategory.BAKERY: 1.8,
    FoodCategory.PHARMACEUTICAL_BIOLOGICS: 3.0,
}

# FDA Food Code Critical Limits
DANGER_ZONE_MIN_C = 4.4   # 40°F
DANGER_ZONE_MAX_C = 60.0  # 140°F
MAX_ACCUMULATED_DANGER_MINUTES = 240.0  # 4-hour rule for TCS foods
WARNING_DANGER_MINUTES = 90.0           # 1.5-hour warning threshold


class KineticsEngine:
    """
    Computes dynamic remaining shelf life (RSL) and spoilage index
    based on continuous IoT temperature and humidity telemetry.
    """

    @staticmethod
    def get_q10(category: FoodCategory) -> float:
        return Q10_FACTORS.get(category, 2.5)

    @classmethod
    def calculate_spoilage_rate_multiplier(
        cls, current_temp_c: float, ref_temp_c: float, category: FoodCategory
    ) -> float:
        """
        Calculates degradation acceleration relative to nominal reference storage temperature.
        Using Q10 relation: acceleration = Q10 ** ((T - T_ref) / 10)
        """
        q10 = cls.get_q10(category)
        delta_t = current_temp_c - ref_temp_c
        # Prevent numerical explosion on extreme outliers
        delta_t = max(-20.0, min(delta_t, 40.0))
        return math.pow(q10, delta_t / 10.0)

    @classmethod
    def evaluate_telemetry_stream(
        cls,
        telemetry: List[IoTTelemetry],
        category: FoodCategory,
        nominal_shelf_life_days: float,
        ref_temp_c: float = 4.0,
        default_interval_minutes: float = 15.0
    ) -> Tuple[float, float, float, SafetyStatus]:
        """
        Evaluates an entire time-series telemetry log.
        Returns:
            - kinetic_spoilage_index (KSI): 0.0 (fresh) to 1.0 (end of life), >1.0 spoiled
            - effective_rsl_hours: Remaining usable hours at current temperature
            - cumulative_danger_zone_minutes: Minutes spent in 4.4°C - 60°C
            - safety_status: Categorized safety state
        """
        nominal_hours = max(1.0, nominal_shelf_life_days * 24.0)
        
        if not telemetry:
            return 0.0, nominal_hours, 0.0, SafetyStatus.OPTIMAL

        accumulated_effective_hours_used = 0.0
        cumulative_danger_zone_minutes = 0.0

        for reading in telemetry:
            temp = reading.temperature_c
            interval_hours = default_interval_minutes / 60.0

            # Danger zone monitoring
            if DANGER_ZONE_MIN_C <= temp <= DANGER_ZONE_MAX_C:
                cumulative_danger_zone_minutes += default_interval_minutes

            # Multiplier for kinetic decay
            multiplier = cls.calculate_spoilage_rate_multiplier(temp, ref_temp_c, category)
            accumulated_effective_hours_used += interval_hours * multiplier

        # Compute Kinetic Spoilage Index (KSI)
        ksi = min(2.0, accumulated_effective_hours_used / nominal_hours)
        remaining_fraction = max(0.0, 1.0 - ksi)

        # Current temperature decay rate to project remaining hours
        latest_temp = telemetry[-1].temperature_c
        current_multiplier = cls.calculate_spoilage_rate_multiplier(latest_temp, ref_temp_c, category)
        effective_rsl_hours = max(0.0, (remaining_fraction * nominal_hours) / max(0.1, current_multiplier))

        # Determine Safety Status based on FDA TCS rules + Biochemical decay
        if cumulative_danger_zone_minutes >= MAX_ACCUMULATED_DANGER_MINUTES:
            status = SafetyStatus.HAZARDOUS_UNSAFE
        elif ksi >= 0.95 or effective_rsl_hours <= 2.0:
            status = SafetyStatus.HAZARDOUS_UNSAFE
        elif cumulative_danger_zone_minutes >= WARNING_DANGER_MINUTES or ksi >= 0.70 or effective_rsl_hours <= 12.0:
            status = SafetyStatus.HIGH_RISK_SALVAGEABLE
        elif ksi >= 0.45 or latest_temp > (ref_temp_c + 3.0):
            status = SafetyStatus.EXCURSION_WARNING
        elif ksi >= 0.25:
            status = SafetyStatus.MONITOR
        else:
            status = SafetyStatus.OPTIMAL

        return round(ksi, 4), round(effective_rsl_hours, 1), round(cumulative_danger_zone_minutes, 1), status
