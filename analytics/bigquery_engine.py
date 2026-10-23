"""
EcoLogix AI - Google Cloud BigQuery Analytics & ESG Accounting Engine
Defines BigQuery schemas, real-time streaming ingestion simulation,
Scope 1/3 GHG carbon abatement calculations, and analytical SQL templates.
"""

import json
from typing import List, Dict, Any
from core.models import AllocationPlan, AuditLogEntry, FoodCategory


# BigQuery DDL Table Schemas
BIGQUERY_SCHEMA_DDL = """
-- Google Cloud BigQuery DDL for EcoLogix Autonomous Cold-Chain Intelligence

CREATE SCHEMA IF NOT EXISTS `ecologix_enterprise_dw`
OPTIONS (
  location = "us-central1",
  description = "Cold-chain telemetry, multi-agent triage, and ESG carbon abatement data warehouse"
);

-- 1. IoT Cold-Chain Telemetry Partitioned Stream
CREATE TABLE IF NOT EXISTS `ecologix_enterprise_dw.iot_coldchain_telemetry` (
  reading_id STRING NOT NULL,
  batch_id STRING NOT NULL,
  timestamp TIMESTAMP NOT NULL,
  temperature_c FLOAT64 NOT NULL,
  humidity_pct FLOAT64,
  ambient_temp_c FLOAT64,
  door_open_duration_sec INT64,
  vibration_g FLOAT64,
  location GEOGRAPHY,
  danger_zone_active BOOL
)
PARTITION BY DATE(timestamp)
CLUSTER BY batch_id;

-- 2. ESG & Carbon Abatement Ledger Table
CREATE TABLE IF NOT EXISTS `ecologix_enterprise_dw.esg_carbon_abatement` (
  plan_id STRING NOT NULL,
  batch_id STRING NOT NULL,
  category STRING NOT NULL,
  quantity_kg FLOAT64 NOT NULL,
  source_location STRING,
  recipient_id STRING,
  recipient_type STRING,
  distance_km FLOAT64,
  co2e_abated_kg FLOAT64 NOT NULL,
  meals_provided INT64 NOT NULL,
  economic_value_saved_usd FLOAT64 NOT NULL,
  water_saved_liters FLOAT64 NOT NULL,
  haccp_compliant BOOL NOT NULL,
  hitl_approved BOOL NOT NULL,
  created_at TIMESTAMP NOT NULL,
  verification_hash STRING NOT NULL
)
PARTITION BY DATE(created_at)
CLUSTER BY recipient_type, category;

-- 3. Cryptographic Tamper-Evident HACCP Audit Ledger Table
CREATE TABLE IF NOT EXISTS `ecologix_enterprise_dw.haccp_audit_ledger` (
  log_id STRING NOT NULL,
  timestamp TIMESTAMP NOT NULL,
  actor_id STRING NOT NULL,
  actor_role STRING NOT NULL,
  action_type STRING NOT NULL,
  batch_id STRING,
  details JSON,
  previous_hash STRING NOT NULL,
  current_hash STRING NOT NULL
)
PARTITION BY DATE(timestamp)
CLUSTER BY actor_role, action_type;
"""

ANALYTICAL_ESG_QUERY = """
-- BigQuery Analytics Query: Executive ESG Abatement & Food Rescue Impact
SELECT
  category,
  COUNT(DISTINCT batch_id) AS total_batches_triaged,
  ROUND(SUM(quantity_kg), 1) AS total_kg_diverted,
  SUM(meals_provided) AS total_meals_served,
  ROUND(SUM(co2e_abated_kg) / 1000.0, 2) AS co2e_abated_metric_tons,
  ROUND(SUM(economic_value_saved_usd), 2) AS economic_value_salvaged_usd,
  ROUND(SUM(water_saved_liters) / 1000.0, 1) AS water_saved_m3
FROM
  `ecologix_enterprise_dw.esg_carbon_abatement`
WHERE
  haccp_compliant = TRUE
GROUP BY
  category
ORDER BY
  total_kg_diverted DESC;
"""


class BigQueryAnalyticsEngine:
    """
    Simulates Google BigQuery streaming buffer and calculates enterprise ESG impact metrics.
    """

    WATER_FOOTPRINT_LITERS_PER_KG = {
        FoodCategory.DAIRY: 1020.0,
        FoodCategory.PRODUCE: 322.0,
        FoodCategory.MEAT_POULTRY: 4325.0,
        FoodCategory.SEAFOOD: 1974.0,
        FoodCategory.PREPARED_MEALS: 850.0,
        FoodCategory.BAKERY: 650.0,
        FoodCategory.PHARMACEUTICAL_BIOLOGICS: 50.0,
    }

    @classmethod
    def format_plan_for_bigquery(cls, plan: AllocationPlan) -> Dict[str, Any]:
        """
        Formats AllocationPlan into BigQuery streaming ingestion row.
        """
        water_rate = cls.WATER_FOOTPRINT_LITERS_PER_KG.get(plan.batch_category, 500.0)
        water_saved = round(plan.quantity_kg * water_rate, 1)

        return {
            "plan_id": plan.plan_id,
            "batch_id": plan.batch_id,
            "category": plan.batch_category.value,
            "quantity_kg": plan.quantity_kg,
            "source_location": plan.source_location,
            "recipient_id": plan.recipient_id,
            "recipient_type": plan.recipient_type,
            "distance_km": plan.distance_km,
            "co2e_abated_kg": plan.co2e_abated_kg,
            "meals_provided": plan.meals_provided,
            "economic_value_saved_usd": plan.economic_value_saved_usd,
            "water_saved_liters": water_saved,
            "haccp_compliant": plan.haccp_compliant,
            "hitl_approved": plan.hitl_approved,
            "created_at": plan.created_at,
            "verification_hash": plan.verification_hash,
        }

    @classmethod
    def aggregate_esg_impact(cls, plans: List[AllocationPlan]) -> Dict[str, Any]:
        """
        Computes system-wide aggregate ESG impact.
        """
        total_kg = 0.0
        total_meals = 0
        total_co2e_kg = 0.0
        total_usd = 0.0
        total_water_liters = 0.0

        for plan in plans:
            if plan.haccp_compliant:
                total_kg += plan.quantity_kg
                total_meals += plan.meals_provided
                total_co2e_kg += plan.co2e_abated_kg
                total_usd += plan.economic_value_saved_usd
                rate = cls.WATER_FOOTPRINT_LITERS_PER_KG.get(plan.batch_category, 500.0)
                total_water_liters += plan.quantity_kg * rate

        return {
            "total_salvaged_kg": round(total_kg, 1),
            "total_meals_provided": total_meals,
            "total_co2e_abated_kg": round(total_co2e_kg, 1),
            "total_co2e_abated_metric_tons": round(total_co2e_kg / 1000.0, 2),
            "total_economic_value_saved_usd": round(total_usd, 2),
            "total_water_saved_m3": round(total_water_liters / 1000.0, 2),
            "equivalent_passenger_cars_off_road_days": round(total_co2e_kg / 12.5, 1),
        }
