"""
EcoLogix AI - Core Data Models
Pydantic schemas for Cold-Chain Telemetry, Inventory Batches, Facilities, HACCP Rules, and Agent Transactions.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import datetime


class FoodCategory(str, Enum):
    DAIRY = "DAIRY"
    PRODUCE = "PRODUCE"
    MEAT_POULTRY = "MEAT_POULTRY"
    SEAFOOD = "SEAFOOD"
    PREPARED_MEALS = "PREPARED_MEALS"
    BAKERY = "BAKERY"
    PHARMACEUTICAL_BIOLOGICS = "PHARMACEUTICAL_BIOLOGICS"


class StorageCondition(str, Enum):
    FROZEN = "FROZEN"                # <= -18°C
    REFRIGERATED = "REFRIGERATED"    # 0°C to 4°C
    CONTROLLED_ROOM = "CONTROLLED_ROOM"  # 15°C to 25°C
    AMBIENT = "AMBIENT"


class SafetyStatus(str, Enum):
    OPTIMAL = "OPTIMAL"
    MONITOR = "MONITOR"
    EXCURSION_WARNING = "EXCURSION_WARNING"
    HIGH_RISK_SALVAGEABLE = "HIGH_RISK_SALVAGEABLE"
    HAZARDOUS_UNSAFE = "HAZARDOUS_UNSAFE"
    CONDEMNED = "CONDEMNED"


class ActionRecommendation(str, Enum):
    MAINTAIN_MONITORING = "MAINTAIN_MONITORING"
    COOLING_OPTIMIZATION = "COOLING_OPTIMIZATION"
    RAPID_RETAIL_MARKDOWN = "RAPID_RETAIL_MARKDOWN"
    EMERGENCY_FOOD_BANK_DISPATCH = "EMERGENCY_FOOD_BANK_DISPATCH"
    SECONDARY_PROCESSING_KITCHEN = "SECONDARY_PROCESSING_KITCHEN"
    ANAEROBIC_DIGESTION_BIOGAS = "ANAEROBIC_DIGESTION_BIOGAS"
    BIOHAZARD_DISPOSAL = "BIOHAZARD_DISPOSAL"


class UserRole(str, Enum):
    SYSTEM_AGENT = "SYSTEM_AGENT"
    COLD_CHAIN_OPERATOR = "COLD_CHAIN_OPERATOR"
    LOGISTICS_COORDINATOR = "LOGISTICS_COORDINATOR"
    FOOD_SAFETY_OFFICER = "FOOD_SAFETY_OFFICER"
    ESG_AUDITOR = "ESG_AUDITOR"


class IoTTelemetry(BaseModel):
    timestamp: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    temperature_c: float
    humidity_pct: float
    ambient_temp_c: Optional[float] = 22.0
    door_open_duration_sec: int = 0
    vibration_g: float = 0.0
    location_lat: float
    location_lon: float


class InventoryBatch(BaseModel):
    batch_id: str
    product_name: str
    category: FoodCategory
    initial_qty_kg: float
    current_qty_kg: float
    unit_cost_usd: float
    storage_condition: StorageCondition
    max_safe_temp_c: float
    min_safe_temp_c: float
    nominal_shelf_life_days: float
    pack_date: str
    printed_expiry: str
    origin_facility: str
    current_location_name: str
    current_lat: float
    current_lon: float
    allergens: List[str] = []
    telemetry_history: List[IoTTelemetry] = []
    
    # Dynamic Kinetic Metrics
    kinetic_spoilage_index: float = 0.0  # 0.0 (Fresh) to 1.0 (Spoiled)
    effective_rsl_hours: float = 0.0     # Remaining Shelf Life in hours
    danger_zone_minutes: float = 0.0     # Cumulative time in 4.4°C - 60°C
    safety_status: SafetyStatus = SafetyStatus.OPTIMAL
    last_evaluated: Optional[str] = None


class RecipientHub(BaseModel):
    hub_id: str
    name: str
    hub_type: str  # "FOOD_BANK", "SHELTER", "COMMUNITY_KITCHEN", "BIOGAS_DIGESTER"
    address: str
    lat: float
    lon: float
    capacity_kg: float
    has_cold_storage: bool
    cold_storage_capacity_kg: float
    current_occupancy_kg: float
    urgency_score: float  # 0.0 to 1.0 (1.0 = severe food insecurity)
    accepted_categories: List[FoodCategory]
    operating_hours: str
    contact_phone: str


class AllocationPlan(BaseModel):
    plan_id: str
    batch_id: str
    batch_product: str
    batch_category: FoodCategory
    quantity_kg: float
    source_location: str
    recipient_id: str
    recipient_name: str
    recipient_type: str
    distance_km: float
    estimated_transit_time_min: float
    cold_chain_maintained_in_transit: bool
    recommended_action: ActionRecommendation
    ai_reasoning: str
    co2e_abated_kg: float
    meals_provided: int
    economic_value_saved_usd: float
    haccp_compliant: bool
    haccp_validation_notes: List[str]
    hitl_required: bool
    hitl_approved: bool = False
    hitl_approved_by: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    verification_hash: str = ""


class AuditLogEntry(BaseModel):
    log_id: str
    timestamp: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    actor_id: str
    actor_role: UserRole
    action_type: str
    batch_id: Optional[str] = None
    details: Dict[str, Any]
    previous_hash: str
    current_hash: str
