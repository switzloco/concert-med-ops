from __future__ import annotations
import json
from datetime import datetime, date
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, field_validator, field_serializer


# Helper to handle JSON load/loads validation safely
def safe_json_load(v, default):
    if isinstance(v, str):
        try:
            return json.loads(v)
        except Exception:
            return default
    return v


# ── Nested Models ────────────────────────────────────────────────────────────

class VitalSigns(BaseModel):
    hr: Optional[int] = None           # heart rate (bpm)
    bp: Optional[str] = None           # blood pressure (e.g. "120/80")
    temp_f: Optional[float] = None     # temperature in F
    spo2: Optional[int] = None         # oxygen saturation (%)
    rr: Optional[int] = None           # respiratory rate
    gcs: Optional[int] = None          # Glasgow Coma Scale (3-15)
    pupils: Optional[str] = None       # e.g., "PERRL", "sluggish", "pinpoint", "dilated"
    skin_condition: Optional[str] = None  # e.g., "warm, dry", "cool, clammy", "diaphoretic"


class SubstanceReported(BaseModel):
    name: str
    route: Optional[str] = None        # e.g., "oral", "insufflation", "inhalation"
    time_taken: Optional[str] = None   # e.g., "2 hours ago", "22:00"
    amount: Optional[str] = None       # e.g., "1 pill", "0.1g"


class Intervention(BaseModel):
    action: str
    time: Optional[str] = None         # e.g., "14:22" or ISO datetime
    by_whom: Optional[str] = None      # staff call_sign or name
    notes: Optional[str] = None


# ── Event ────────────────────────────────────────────────────────────────────

class EventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    event_id: str
    name: str
    venue: Optional[str] = None
    date_start: Optional[datetime] = None
    date_end: Optional[datetime] = None
    expected_attendance: Optional[int] = None
    medical_lead: Optional[str] = None
    contact_info: Optional[str] = None
    weather_high_f: Optional[float] = None
    weather_humidity: Optional[float] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None


class EventCreate(BaseModel):
    name: str
    venue: Optional[str] = None
    date_start: Optional[datetime] = None
    date_end: Optional[datetime] = None
    expected_attendance: Optional[int] = None
    medical_lead: Optional[str] = None
    contact_info: Optional[str] = None
    weather_high_f: Optional[float] = None
    weather_humidity: Optional[float] = None
    notes: Optional[str] = None


class EventUpdate(BaseModel):
    name: Optional[str] = None
    venue: Optional[str] = None
    date_start: Optional[datetime] = None
    date_end: Optional[datetime] = None
    expected_attendance: Optional[int] = None
    medical_lead: Optional[str] = None
    contact_info: Optional[str] = None
    weather_high_f: Optional[float] = None
    weather_humidity: Optional[float] = None
    notes: Optional[str] = None


# ── StaffMember ──────────────────────────────────────────────────────────────

class StaffMemberRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    staff_id: str
    event_id: str
    name: str
    role: str
    call_sign: str
    is_on_shift: bool
    created_at: Optional[datetime] = None


class StaffMemberCreate(BaseModel):
    event_id: str
    name: str
    role: str  # "emt" | "paramedic" | "rn" | "md" | "supervisor"
    call_sign: str
    is_on_shift: bool = True


class StaffMemberUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    call_sign: Optional[str] = None
    is_on_shift: Optional[bool] = None


# ── Patient ──────────────────────────────────────────────────────────────────

class PatientRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    patient_id: str
    event_id: str
    identifier: str
    approx_age: Optional[int] = None
    gender: Optional[str] = None
    weight_kg: Optional[float] = None
    known_allergies: List[str] = []
    known_medications: List[str] = []
    known_conditions: List[str] = []
    substances_reported: List[SubstanceReported] = []
    location_found: str
    is_active: bool
    created_at: Optional[datetime] = None

    @field_validator("known_allergies", "known_medications", "known_conditions", mode="before")
    @classmethod
    def parse_json_list(cls, v):
        return safe_json_load(v, [])

    @field_validator("substances_reported", mode="before")
    @classmethod
    def parse_substances_reported(cls, v):
        parsed = safe_json_load(v, [])
        return [SubstanceReported(**item) if isinstance(item, dict) else item for item in parsed]


class PatientCreate(BaseModel):
    event_id: str
    identifier: str  # wristband # or physical description
    approx_age: Optional[int] = None
    gender: Optional[str] = None
    weight_kg: Optional[float] = None
    known_allergies: Optional[List[str]] = []
    known_medications: Optional[List[str]] = []
    known_conditions: Optional[List[str]] = []
    substances_reported: Optional[List[SubstanceReported]] = []
    location_found: str = "other"  # "venue_tent" | "campground" | "gate" | "field" | "other"


class PatientUpdate(BaseModel):
    identifier: Optional[str] = None
    approx_age: Optional[int] = None
    gender: Optional[str] = None
    weight_kg: Optional[float] = None
    known_allergies: Optional[List[str]] = None
    known_medications: Optional[List[str]] = None
    known_conditions: Optional[List[str]] = None
    substances_reported: Optional[List[SubstanceReported]] = None
    location_found: Optional[str] = None
    is_active: Optional[bool] = None


# ── Encounter ────────────────────────────────────────────────────────────────

class EncounterRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    encounter_id: str
    event_id: str
    patient_id: str
    doc_type: str
    logged_by: str
    encounter_time: datetime
    chief_complaint: Optional[str] = None
    symptoms: List[str] = []
    vital_signs: Dict[str, Any] = {}
    substances_involved: List[str] = []
    triage_level: str
    escalated_to: Optional[str] = None
    escalation_time: Optional[datetime] = None
    interventions: List[Dict[str, Any]] = []
    disposition: str
    transport_hospital: Optional[str] = None
    transport_unit: Optional[str] = None
    transport_time: Optional[datetime] = None
    ama_documented: bool = False
    ama_capacity_assessment: Optional[str] = None
    ai_response: Optional[str] = None
    ai_model_used: Optional[str] = None
    photo_paths: List[str] = []
    notes: Optional[str] = None
    created_at: Optional[datetime] = None

    @field_validator("symptoms", "substances_involved", "photo_paths", mode="before")
    @classmethod
    def parse_symptoms(cls, v):
        return safe_json_load(v, [])

    @field_validator("vital_signs", mode="before")
    @classmethod
    def parse_vital_signs(cls, v):
        return safe_json_load(v, {})

    @field_validator("interventions", mode="before")
    @classmethod
    def parse_interventions(cls, v):
        return safe_json_load(v, [])


class EncounterCreate(BaseModel):
    event_id: str
    patient_id: str
    doc_type: str  # "pcr" | "otc"
    logged_by: str  # staff_id
    encounter_time: Optional[datetime] = None
    chief_complaint: Optional[str] = None
    symptoms: Optional[List[str]] = []
    vital_signs: Optional[VitalSigns] = None
    substances_involved: Optional[List[str]] = []
    triage_level: str = "green"  # "green" | "yellow" | "red" | "black"
    escalated_to: Optional[str] = None
    escalation_time: Optional[datetime] = None
    interventions: Optional[List[Intervention]] = []
    disposition: str = "released"  # "released" | "observation" | "transport" | "ama" | "deceased"
    transport_hospital: Optional[str] = None
    transport_unit: Optional[str] = None
    transport_time: Optional[datetime] = None
    ama_documented: Optional[bool] = False
    ama_capacity_assessment: Optional[str] = None
    photo_paths: Optional[List[str]] = []
    notes: Optional[str] = None


class EncounterUpdate(BaseModel):
    chief_complaint: Optional[str] = None
    symptoms: Optional[List[str]] = None
    vital_signs: Optional[VitalSigns] = None
    substances_involved: Optional[List[str]] = None
    triage_level: Optional[str] = None
    escalated_to: Optional[str] = None
    escalation_time: Optional[datetime] = None
    interventions: Optional[List[Intervention]] = None
    disposition: Optional[str] = None
    transport_hospital: Optional[str] = None
    transport_unit: Optional[str] = None
    transport_time: Optional[datetime] = None
    ama_documented: Optional[bool] = None
    ama_capacity_assessment: Optional[str] = None
    photo_paths: Optional[List[str]] = None
    notes: Optional[str] = None


# ── IncidentQueue ────────────────────────────────────────────────────────────

class IncidentQueueRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    incident_id: str
    event_id: str
    patient_id: str
    encounter_id: Optional[str] = None
    status: str
    assigned_to: str
    location: str
    priority: str
    dispatch_time: datetime
    arrival_time: Optional[datetime] = None
    cleared_time: Optional[datetime] = None
    radio_notes: Optional[str] = None
    created_at: Optional[datetime] = None


class IncidentQueueCreate(BaseModel):
    event_id: str
    patient_id: str
    encounter_id: Optional[str] = None
    assigned_to: str  # staff_id
    location: str     # "stage_left" | "stage_right" | "campground_a" | "campground_b" | "gate" | "medical_tent" | "other"
    priority: str     # "green" | "yellow" | "red" | "black"
    radio_notes: Optional[str] = None


class IncidentQueueUpdate(BaseModel):
    status: Optional[str] = None  # "dispatched" | "en_route" | "on_scene" | "in_tent" | "observation" | "cleared"
    assigned_to: Optional[str] = None
    location: Optional[str] = None
    priority: Optional[str] = None
    encounter_id: Optional[str] = None
    arrival_time: Optional[datetime] = None
    cleared_time: Optional[datetime] = None
    radio_notes: Optional[str] = None


# ── HospitalDirectory ────────────────────────────────────────────────────────

class HospitalDirectoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    hospital_id: str
    name: str
    distance_miles: Optional[float] = None
    drive_time_min: Optional[int] = None
    trauma_level: Optional[int] = None
    capabilities: List[str] = []
    phone: Optional[str] = None
    address: Optional[str] = None
    is_on_diversion: bool = False
    notes: Optional[str] = None

    @field_validator("capabilities", mode="before")
    @classmethod
    def parse_capabilities(cls, v):
        return safe_json_load(v, [])


class HospitalDirectoryCreate(BaseModel):
    name: str
    distance_miles: Optional[float] = None
    drive_time_min: Optional[int] = None
    trauma_level: Optional[int] = None
    capabilities: Optional[List[str]] = []
    phone: Optional[str] = None
    address: Optional[str] = None
    is_on_diversion: bool = False
    notes: Optional[str] = None


class HospitalDirectoryUpdate(BaseModel):
    name: Optional[str] = None
    distance_miles: Optional[float] = None
    drive_time_min: Optional[int] = None
    trauma_level: Optional[int] = None
    capabilities: Optional[List[str]] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    is_on_diversion: Optional[bool] = None
    notes: Optional[str] = None


# ── ReagentLog ───────────────────────────────────────────────────────────────

class ReagentLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    log_id: str
    event_id: str
    patient_id: Optional[str] = None
    sample_description: str
    test_type: str
    test_result: str
    color_observed: Optional[str] = None
    predicted_substance: Optional[str] = None
    disclaimer_agreed: bool
    tester_staff_id: str
    created_at: Optional[datetime] = None


class ReagentLogCreate(BaseModel):
    event_id: str
    patient_id: Optional[str] = None
    sample_description: str
    test_type: str  # "fent_strip" | "marquis" | "mecke" | "mandelin" | "folin" | "ehhrlich" | "ftir"
    test_result: str  # "positive" | "negative" | "color_change_verified" | "inconclusive"
    color_observed: Optional[str] = None
    predicted_substance: Optional[str] = None
    disclaimer_agreed: bool
    tester_staff_id: str  # staff_id

    @field_validator("disclaimer_agreed")
    @classmethod
    def check_disclaimer(cls, v: bool) -> bool:
        if not v:
            raise ValueError("You must read and agree to the liability disclaimer before logging drug testing results.")
        return v


# ── Supply ───────────────────────────────────────────────────────────────────

class SupplyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    supply_id: str
    event_id: str
    name: str
    category: str
    quantity_start: int
    quantity_used: int
    quantity_remaining: int
    expiration_date: Optional[date] = None
    lot_number: Optional[str] = None
    location: str
    notes: Optional[str] = None


class SupplyCreate(BaseModel):
    event_id: str
    name: str
    category: str  # "medication" | "equipment" | "ppe" | "narcan" | "iv_fluid" | "reagent"
    quantity_start: int
    quantity_used: int = 0
    quantity_remaining: int
    expiration_date: Optional[date] = None
    lot_number: Optional[str] = None
    location: str = "venue_tent"  # "venue_tent" | "campground" | "rover_kit"
    notes: Optional[str] = None


class SupplyUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    quantity_start: Optional[int] = None
    quantity_used: Optional[int] = None
    quantity_remaining: Optional[int] = None
    expiration_date: Optional[date] = None
    lot_number: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None


# ── AI Query / Chat Models ───────────────────────────────────────────────────

class TriageQueryRequest(BaseModel):
    patient_id: str
    current_symptoms: List[str]
    vitals: Optional[VitalSigns] = None
    reported_substances: Optional[List[SubstanceReported]] = []
    notes: Optional[str] = None


class TransportDecisionRequest(BaseModel):
    patient_id: str
    current_symptoms: List[str]
    vitals: Optional[VitalSigns] = None
    triage_level: str
    closest_hospital_id: str
    ambulance_status: Optional[str] = None  # e.g., "1 ambulance available", "none"
    notes: Optional[str] = None


class DrugInteractionQueryRequest(BaseModel):
    substances: List[str]


class ExtractEncounterRequest(BaseModel):
    text: str
    event_id: str
