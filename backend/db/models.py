import uuid
from datetime import datetime
from sqlalchemy import (
    Boolean, CheckConstraint, Column, DateTime, Date, Float,
    ForeignKey, Integer, String, Text
)
from sqlalchemy.orm import relationship
from backend.db.database import Base


def _uuid():
    return str(uuid.uuid4())


class Event(Base):
    __tablename__ = "events"

    event_id = Column(String, primary_key=True, default=_uuid)
    name = Column(String, nullable=False)
    venue = Column(String)
    date_start = Column(DateTime)
    date_end = Column(DateTime)
    expected_attendance = Column(Integer)
    medical_lead = Column(String)
    contact_info = Column(String)
    weather_high_f = Column(Float)
    weather_humidity = Column(Float)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    staff_members = relationship("StaffMember", back_populates="event", cascade="all, delete-orphan")
    patients = relationship("Patient", back_populates="event", cascade="all, delete-orphan")
    encounters = relationship("Encounter", back_populates="event", cascade="all, delete-orphan")
    incidents = relationship("IncidentQueue", back_populates="event", cascade="all, delete-orphan")
    reagent_logs = relationship("ReagentLog", back_populates="event", cascade="all, delete-orphan")
    supplies = relationship("Supply", back_populates="event", cascade="all, delete-orphan")


class StaffMember(Base):
    __tablename__ = "staff_members"
    __table_args__ = (
        CheckConstraint(
            "role IN ('emt', 'paramedic', 'rn', 'md', 'supervisor')",
            name="ck_staff_role"
        ),
    )

    staff_id = Column(String, primary_key=True, default=_uuid)
    event_id = Column(String, ForeignKey("events.event_id"), nullable=False)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    call_sign = Column(String, nullable=False)  # radio handle, e.g. "Med-3"
    is_on_shift = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    event = relationship("Event", back_populates="staff_members")
    assigned_incidents = relationship("IncidentQueue", back_populates="assigned_staff")
    logged_encounters = relationship("Encounter", foreign_keys="Encounter.logged_by", back_populates="logged_by_staff")
    escalated_encounters = relationship("Encounter", foreign_keys="Encounter.escalated_to", back_populates="escalated_staff")
    tested_logs = relationship("ReagentLog", back_populates="tester")


class Patient(Base):
    __tablename__ = "patients"
    __table_args__ = (
        CheckConstraint(
            "location_found IN ('venue_tent', 'campground', 'gate', 'field', 'other')",
            name="ck_patient_location"
        ),
    )

    patient_id = Column(String, primary_key=True, default=_uuid)
    event_id = Column(String, ForeignKey("events.event_id"), nullable=False)
    identifier = Column(String, nullable=False)  # wristband # or physical description, NOT legal name
    approx_age = Column(Integer)
    gender = Column(String)
    weight_kg = Column(Float)
    known_allergies = Column(Text, default="[]")        # JSON array
    known_medications = Column(Text, default="[]")      # JSON array
    known_conditions = Column(Text, default="[]")       # JSON array
    substances_reported = Column(Text, default="[]")    # JSON array of objects
    location_found = Column(String, nullable=False, default="other")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    event = relationship("Event", back_populates="patients")
    encounters = relationship("Encounter", back_populates="patient", cascade="all, delete-orphan")
    incidents = relationship("IncidentQueue", back_populates="patient", cascade="all, delete-orphan")
    reagent_logs = relationship("ReagentLog", back_populates="patient")


class Encounter(Base):
    __tablename__ = "encounters"
    __table_args__ = (
        CheckConstraint("doc_type IN ('pcr', 'otc')", name="ck_encounter_doc_type"),
        CheckConstraint("triage_level IN ('green', 'yellow', 'red', 'black')", name="ck_encounter_triage_level"),
        CheckConstraint(
            "disposition IN ('released', 'observation', 'transport', 'ama', 'deceased')",
            name="ck_encounter_disposition"
        ),
    )

    encounter_id = Column(String, primary_key=True, default=_uuid)
    event_id = Column(String, ForeignKey("events.event_id"), nullable=False)
    patient_id = Column(String, ForeignKey("patients.patient_id"), nullable=False)
    doc_type = Column(String, nullable=False, default="pcr")  # "pcr" or "otc"
    logged_by = Column(String, ForeignKey("staff_members.staff_id"), nullable=False)
    encounter_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    chief_complaint = Column(Text)
    symptoms = Column(Text, default="[]")  # JSON array
    vital_signs = Column(Text, default="{}")  # JSON: {hr, bp, temp_f, spo2, rr, gcs, pupils, skin_condition}
    substances_involved = Column(Text, default="[]")  # JSON array
    triage_level = Column(String, nullable=False, default="green")
    escalated_to = Column(String, ForeignKey("staff_members.staff_id"), nullable=True)
    escalation_time = Column(DateTime, nullable=True)
    interventions = Column(Text, default="[]")  # JSON: [{action, time, by_whom, notes}]
    disposition = Column(String, nullable=False, default="released")
    transport_hospital = Column(String, nullable=True)  # Name of hospital
    transport_unit = Column(String, nullable=True)      # ambulance unit ID
    transport_time = Column(DateTime, nullable=True)
    ama_documented = Column(Boolean, default=False)
    ama_capacity_assessment = Column(Text, nullable=True)
    ai_response = Column(Text, nullable=True)
    ai_model_used = Column(String, nullable=True)
    photo_paths = Column(Text, default="[]")  # JSON array of local photo paths
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    event = relationship("Event", back_populates="encounters")
    patient = relationship("Patient", back_populates="encounters")
    logged_by_staff = relationship("StaffMember", foreign_keys=[logged_by], back_populates="logged_encounters")
    escalated_staff = relationship("StaffMember", foreign_keys=[escalated_to], back_populates="escalated_encounters")
    incidents = relationship("IncidentQueue", back_populates="encounter")


class IncidentQueue(Base):
    __tablename__ = "incident_queue"
    __table_args__ = (
        CheckConstraint(
            "status IN ('dispatched', 'en_route', 'on_scene', 'in_tent', 'observation', 'cleared')",
            name="ck_incident_status"
        ),
        CheckConstraint("priority IN ('green', 'yellow', 'red', 'black')", name="ck_incident_priority"),
        CheckConstraint(
            "location IN ('stage_left', 'stage_right', 'campground_a', 'campground_b', 'gate', 'medical_tent', 'other')",
            name="ck_incident_location"
        ),
    )

    incident_id = Column(String, primary_key=True, default=_uuid)
    event_id = Column(String, ForeignKey("events.event_id"), nullable=False)
    patient_id = Column(String, ForeignKey("patients.patient_id"), nullable=False)
    encounter_id = Column(String, ForeignKey("encounters.encounter_id"), nullable=True)
    status = Column(String, nullable=False, default="dispatched")
    assigned_to = Column(String, ForeignKey("staff_members.staff_id"), nullable=False)
    location = Column(String, nullable=False, default="other")
    priority = Column(String, nullable=False, default="green")
    dispatch_time = Column(DateTime, default=datetime.utcnow)
    arrival_time = Column(DateTime, nullable=True)
    cleared_time = Column(DateTime, nullable=True)
    radio_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    event = relationship("Event", back_populates="incidents")
    patient = relationship("Patient", back_populates="incidents")
    encounter = relationship("Encounter", back_populates="incidents")
    assigned_staff = relationship("StaffMember", back_populates="assigned_incidents")


class HospitalDirectory(Base):
    __tablename__ = "hospital_directory"

    hospital_id = Column(String, primary_key=True, default=_uuid)
    name = Column(String, nullable=False)
    distance_miles = Column(Float)
    drive_time_min = Column(Integer)
    trauma_level = Column(Integer, nullable=True)  # e.g., 1, 2, 3, or null
    capabilities = Column(Text, default="[]")  # JSON: ["cardiac", "peds", "burn", "psych"]
    phone = Column(String)
    address = Column(String)
    is_on_diversion = Column(Boolean, default=False)
    notes = Column(Text)


class ReagentLog(Base):
    __tablename__ = "reagent_logs"
    __table_args__ = (
        CheckConstraint(
            "test_type IN ('fent_strip', 'marquis', 'mecke', 'mandelin', 'folin', 'ehhrlich', 'ftir')",
            name="ck_reagent_test_type"
        ),
        CheckConstraint(
            "test_result IN ('positive', 'negative', 'color_change_verified', 'inconclusive')",
            name="ck_reagent_test_result"
        ),
    )

    log_id = Column(String, primary_key=True, default=_uuid)
    event_id = Column(String, ForeignKey("events.event_id"), nullable=False)
    patient_id = Column(String, ForeignKey("patients.patient_id"), nullable=True)
    sample_description = Column(String, nullable=False)  # e.g., "Pink pill with skull stamp"
    test_type = Column(String, nullable=False)
    test_result = Column(String, nullable=False)
    color_observed = Column(String)
    predicted_substance = Column(String)
    disclaimer_agreed = Column(Boolean, default=False)
    tester_staff_id = Column(String, ForeignKey("staff_members.staff_id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    event = relationship("Event", back_populates="reagent_logs")
    patient = relationship("Patient", back_populates="reagent_logs")
    tester = relationship("StaffMember", back_populates="tested_logs")


class Supply(Base):
    __tablename__ = "supplies"
    __table_args__ = (
        CheckConstraint(
            "category IN ('medication', 'equipment', 'ppe', 'narcan', 'iv_fluid', 'reagent')",
            name="ck_supply_category"
        ),
        CheckConstraint(
            "location IN ('venue_tent', 'campground', 'rover_kit')",
            name="ck_supply_location"
        ),
    )

    supply_id = Column(String, primary_key=True, default=_uuid)
    event_id = Column(String, ForeignKey("events.event_id"), nullable=False)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    quantity_start = Column(Integer, nullable=False)
    quantity_used = Column(Integer, default=0)
    quantity_remaining = Column(Integer, nullable=False)
    expiration_date = Column(Date, nullable=True)
    lot_number = Column(String, nullable=True)
    location = Column(String, nullable=False, default="venue_tent")
    notes = Column(Text, nullable=True)

    event = relationship("Event", back_populates="supplies")
