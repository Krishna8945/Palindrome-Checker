"""
EcoLogix AI - IoT Telemetry & Degradation Sensing Agent
Ingests real-time time-series cold-chain telemetry and calculates dynamic biochemical decay.
"""

from typing import List, Dict, Any, Tuple
from core.models import InventoryBatch, IoTTelemetry, SafetyStatus
from core.kinetics import KineticsEngine


class TelemetryAgent:
    """
    Autonomous agent responsible for continuous stream monitoring,
    anomaly detection, and kinetic degradation recalculation.
    """

    def __init__(self, agent_id: str = "agent-telemetry-01"):
        self.agent_id = agent_id

    def process_new_reading(
        self, batch: InventoryBatch, reading: IoTTelemetry
    ) -> Tuple[InventoryBatch, Dict[str, Any]]:
        """
        Appends new IoT reading and triggers instant re-evaluation of shelf-life kinetics.
        """
        # Append reading to historical trace
        batch.telemetry_history.append(reading)

        # Update current coordinates
        batch.current_lat = reading.location_lat
        batch.current_lon = reading.location_lon

        # Recalculate biochemical degradation kinetics
        ref_temp = 4.0 if batch.storage_condition.value == "REFRIGERATED" else -18.0 if batch.storage_condition.value == "FROZEN" else 20.0
        ksi, rsl_hours, danger_mins, status = KineticsEngine.evaluate_telemetry_stream(
            telemetry=batch.telemetry_history,
            category=batch.category,
            nominal_shelf_life_days=batch.nominal_shelf_life_days,
            ref_temp_c=ref_temp,
            default_interval_minutes=15.0
        )

        old_status = batch.safety_status
        batch.kinetic_spoilage_index = ksi
        batch.effective_rsl_hours = rsl_hours
        batch.danger_zone_minutes = danger_mins
        batch.safety_status = status

        alert_event = {
            "batch_id": batch.batch_id,
            "product": batch.product_name,
            "current_temp": reading.temperature_c,
            "ksi": ksi,
            "effective_rsl_hours": rsl_hours,
            "danger_zone_minutes": danger_mins,
            "old_status": old_status.value,
            "new_status": status.value,
            "status_changed": (old_status != status),
            "is_critical": (status in [SafetyStatus.HIGH_RISK_SALVAGEABLE, SafetyStatus.HAZARDOUS_UNSAFE])
        }

        return batch, alert_event
