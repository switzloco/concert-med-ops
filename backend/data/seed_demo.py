import json
from datetime import datetime, date
from sqlalchemy.orm import Session
from backend.db.database import SessionLocal, engine, Base
from backend.db.models import (
    Event, StaffMember, Patient, Encounter,
    IncidentQueue, HospitalDirectory, ReagentLog, Supply
)


def seed_database(db: Session):
    # Clear existing data to allow clean re-seeds
    db.query(IncidentQueue).delete()
    db.query(Encounter).delete()
    db.query(Patient).delete()
    db.query(StaffMember).delete()
    db.query(Supply).delete()
    db.query(ReagentLog).delete()
    db.query(HospitalDirectory).delete()
    db.query(Event).delete()
    db.commit()

    # 1. Create Event
    event = Event(
        name="Griztronics 2026",
        venue="The Gorge Amphitheatre, George, WA",
        date_start=datetime(2026, 7, 10, 12, 0),
        date_end=datetime(2026, 7, 13, 12, 0),
        expected_attendance=22500,
        medical_lead="Dr. Sarah Jenkins, MD",
        contact_info="Radio: Doc-1 / Phone: (509) 555-0199",
        weather_high_f=85.0,
        weather_humidity=22.0,
        notes="High intoxication risk expected. Main campgrounds active starting Friday morning.",
    )
    db.add(event)
    db.flush()  # Populates event_id

    # 2. Area Hospitals
    hospitals = [
        HospitalDirectory(
            name="Quincy Valley Medical Center",
            distance_miles=24.5,
            drive_time_min=25,
            trauma_level=None,
            capabilities=json.dumps(["general", "imaging"]),
            phone="(509) 787-3531",
            address="908 10th Ave SW, Quincy, WA 98848",
            is_on_diversion=False,
            notes="Closest facility. Limited capabilities; good for simple wound sutures or minor issues.",
        ),
        HospitalDirectory(
            name="Samaritan Hospital",
            distance_miles=42.8,
            drive_time_min=43,
            trauma_level=3,
            capabilities=json.dumps(["general", "cardiac", "imaging", "ortho"]),
            phone="(509) 765-5606",
            address="801 E Wheeler Rd, Moses Lake, WA 98837",
            is_on_diversion=False,
            notes="Level 3 Trauma center. Able to handle moderate-to-severe medical concerns.",
        ),
        HospitalDirectory(
            name="Central Washington Hospital",
            distance_miles=58.2,
            drive_time_min=59,
            trauma_level=3,
            capabilities=json.dumps(["general", "cardiac", "imaging", "icu", "psych"]),
            phone="(509) 662-1511",
            address="1201 S Miller St, Wenatchee, WA 98801",
            is_on_diversion=False,
            notes="Full capability regional center. Has ICU and psych support.",
        ),
        HospitalDirectory(
            name="Harborview Medical Center",
            distance_miles=148.0,
            drive_time_min=180,
            trauma_level=1,
            capabilities=json.dumps(["general", "cardiac", "burn", "neurosurgery", "icu"]),
            phone="(206) 744-3000",
            address="325 9th Ave, Seattle, WA 98104",
            is_on_diversion=False,
            notes="Level 1 Trauma. Reserved strictly for life-threatening neurosurgery or major trauma.",
        ),
    ]
    for h in hospitals:
        db.add(h)

    # 3. Staff Members
    staff = [
        StaffMember(
            event_id=event.event_id,
            name="Dr. Sarah Jenkins",
            role="md",
            call_sign="Doc-1",
            is_on_shift=True,
        ),
        StaffMember(
            event_id=event.event_id,
            name="Marcus Vance",
            role="paramedic",
            call_sign="Med-3",
            is_on_shift=True,
        ),
        StaffMember(
            event_id=event.event_id,
            name="Elena Rostova",
            role="rn",
            call_sign="RN-1",
            is_on_shift=True,
        ),
        StaffMember(
            event_id=event.event_id,
            name="Tyler Kincaid",
            role="emt",
            call_sign="Rover-2",
            is_on_shift=True,
        ),
        StaffMember(
            event_id=event.event_id,
            name="Chloe Bennett",
            role="emt",
            call_sign="Rover-3",
            is_on_shift=True,
        ),
        StaffMember(
            event_id=event.event_id,
            name="Marcus Brody",
            role="supervisor",
            call_sign="Command-1",
            is_on_shift=True,
        ),
    ]
    for s in staff:
        db.add(s)
    db.flush()

    # Create mapping of roles/callsigns to objects
    staff_map = {s.call_sign: s for s in staff}

    # 4. Supplies
    supplies = [
        Supply(
            event_id=event.event_id,
            name="Naloxone (Narcan) Nasal Spray 4mg",
            category="narcan",
            quantity_start=200,
            quantity_used=6,
            quantity_remaining=194,
            expiration_date=date(2028, 5, 1),
            lot_number="NLX-442",
            location="campground",
            notes="Primary kit supplies.",
        ),
        Supply(
            event_id=event.event_id,
            name="IV Normal Saline 0.9% 1000mL",
            category="iv_fluid",
            quantity_start=100,
            quantity_used=18,
            quantity_remaining=82,
            expiration_date=date(2027, 9, 15),
            lot_number="NS-1192",
            location="venue_tent",
        ),
        Supply(
            event_id=event.event_id,
            name="Marquis Reagent Testing Ampoules",
            category="reagent",
            quantity_start=50,
            quantity_used=8,
            quantity_remaining=42,
            expiration_date=date(2027, 2, 10),
            lot_number="MRQ-880",
            location="campground",
        ),
        Supply(
            event_id=event.event_id,
            name="Oral Hydration Electrolyte Packets",
            category="medication",
            quantity_start=600,
            quantity_used=150,
            quantity_remaining=450,
            expiration_date=date(2027, 12, 31),
            lot_number="ELEC-192",
            location="rover_kit",
        ),
        Supply(
            event_id=event.event_id,
            name="Midazolam 5mg/mL Injection Vials",
            category="medication",
            quantity_start=30,
            quantity_used=2,
            quantity_remaining=28,
            expiration_date=date(2027, 6, 20),
            lot_number="MDZ-204",
            location="venue_tent",
            notes="Locked drawer, MD or PMIC access only.",
        ),
    ]
    for sup in supplies:
        db.add(sup)

    # 5. Patients (No real names, only wristbands/descriptions)
    patients = [
        Patient(
            event_id=event.event_id,
            identifier="Pink hair, green crop top, wristband #4921",
            approx_age=22,
            gender="female",
            weight_kg=58.0,
            known_allergies=json.dumps(["Penicillin"]),
            known_medications=json.dumps(["Sertraline (Zoloft) 50mg daily"]),
            known_conditions=json.dumps(["Anxiety"]),
            substances_reported=json.dumps([
                {"name": "MDMA", "route": "oral", "time_taken": "2 hours ago", "amount": "1.5 pills"}
            ]),
            location_found="venue_tent",
            is_active=True,
        ),
        Patient(
            event_id=event.event_id,
            identifier="Male, black tank top, khaki shorts, wristband #1085",
            approx_age=26,
            gender="male",
            weight_kg=82.0,
            known_allergies=json.dumps([]),
            known_medications=json.dumps([]),
            known_conditions=json.dumps([]),
            substances_reported=json.dumps([
                {"name": "Alcohol", "route": "oral", "time_taken": "Ongoing", "amount": "Multiple beers"},
                {"name": "GHB", "route": "oral", "time_taken": "1 hour ago", "amount": "1 cap"}
            ]),
            location_found="campground",
            is_active=True,
        ),
        Patient(
            event_id=event.event_id,
            identifier="Wristband #8832, found somnolent near stage left",
            approx_age=20,
            gender="unknown",
            weight_kg=70.0,
            known_allergies=json.dumps([]),
            known_medications=json.dumps([]),
            known_conditions=json.dumps([]),
            substances_reported=json.dumps([
                {"name": "Suspected Fentanyl / Opioid", "route": "insufflation", "time_taken": "Unknown", "amount": "Unknown"}
            ]),
            location_found="field",
            is_active=True,
        ),
        Patient(
            event_id=event.event_id,
            identifier="Female, glitter cheeks, purple hydration pack, wristband #5531",
            approx_age=23,
            gender="female",
            weight_kg=62.0,
            known_allergies=json.dumps([]),
            known_medications=json.dumps([]),
            known_conditions=json.dumps([]),
            substances_reported=json.dumps([
                {"name": "LSD", "route": "oral", "time_taken": "4 hours ago", "amount": "1 blotter tab"},
                {"name": "MDMA", "route": "oral", "time_taken": "3 hours ago", "amount": "0.1g powder"}
            ]),
            location_found="field",
            is_active=True,
        ),
        Patient(
            event_id=event.event_id,
            identifier="Male, tall, bucket hat, wristband #3928",
            approx_age=28,
            gender="male",
            weight_kg=90.0,
            known_allergies=json.dumps(["Sulfa drugs"]),
            known_medications=json.dumps([]),
            known_conditions=json.dumps([]),
            substances_reported=json.dumps([
                {"name": "Alcohol", "route": "oral", "time_taken": "5 hours", "amount": "Heavy consumption"}
            ]),
            location_found="campground",
            is_active=True,
        ),
    ]
    for p in patients:
        db.add(p)
    db.flush()

    patient_map = {p.identifier.split(",")[0]: p for p in patients}

    # 6. Encounters
    encounters = [
        Encounter(
            event_id=event.event_id,
            patient_id=patient_map["Pink hair"].patient_id,
            doc_type="pcr",
            logged_by=staff_map["Doc-1"].staff_id,
            encounter_time=datetime.utcnow(),
            chief_complaint="Elevated temperature, tachycardia, mild anxiety",
            symptoms=json.dumps(["tachycardia", "hyperthermia", "anxiety", "muscle tightness"]),
            vital_signs=json.dumps({
                "hr": 118,
                "bp": "135/88",
                "temp_f": 101.6,
                "spo2": 98,
                "rr": 18,
                "gcs": 15,
                "pupils": "dilated, reactive",
                "skin_condition": "warm, diaphoretic"
            }),
            substances_involved=json.dumps(["MDMA", "Sertraline"]),
            triage_level="yellow",
            escalated_to=staff_map["Doc-1"].staff_id,
            escalation_time=datetime.utcnow(),
            interventions=json.dumps([
                {"action": "Moved to active cooling area of medical tent", "time": "10:15", "by_whom": "RN-1", "notes": "Stripped excess heavy clothing"},
                {"action": "Evaporative cooling with mist & fan", "time": "10:20", "by_whom": "RN-1", "notes": "Cooled down temp to 100.8F"},
                {"action": "Oral hydration solution administered", "time": "10:30", "by_whom": "Rover-2", "notes": "Drunk 500mL easily"}
            ]),
            disposition="observation",
            notes="Patient is alert and oriented. Mild muscle twitching noted but no sustained clonus. Currently stable under observation.",
        ),
        Encounter(
            event_id=event.event_id,
            patient_id=patient_map["Male"].patient_id,
            doc_type="pcr",
            logged_by=staff_map["Med-3"].staff_id,
            encounter_time=datetime.utcnow(),
            chief_complaint="Drowsiness, ataxia, fluctuating consciousness",
            symptoms=json.dumps(["drowsiness", "ataxia", "nausea"]),
            vital_signs=json.dumps({
                "hr": 64,
                "bp": "110/70",
                "temp_f": 97.8,
                "spo2": 95,
                "rr": 10,
                "gcs": 11,
                "pupils": "constricted, sluggish",
                "skin_condition": "cool, pale"
            }),
            substances_involved=json.dumps(["Alcohol", "GHB"]),
            triage_level="yellow",
            interventions=json.dumps([
                {"action": "Placed in Recovery Position (lateral decubitus)", "time": "09:45", "by_whom": "Med-3", "notes": "Airway protected, suction ready"},
                {"action": "Supplemental oxygen 2L via nasal cannula", "time": "09:50", "by_whom": "Med-3", "notes": "SpO2 improved to 98%"}
            ]),
            disposition="observation",
            notes="Comatose but gag reflex intact. GCS fluctuating between 9 and 12. Monitoring breathing rate closely.",
        ),
        Encounter(
            event_id=event.event_id,
            patient_id=patient_map["Male"].patient_id,  # Tall male
            doc_type="otc",
            logged_by=staff_map["Rover-3"].staff_id,
            encounter_time=datetime.utcnow(),
            chief_complaint="Minor scrape on left forearm",
            symptoms=json.dumps(["abrasion"]),
            vital_signs=json.dumps({}),
            substances_involved=json.dumps(["Alcohol"]),
            triage_level="green",
            interventions=json.dumps([
                {"action": "Cleaned wound and applied adhesive bandage", "time": "08:15", "by_whom": "Rover-3"}
            ]),
            disposition="released",
            notes="Superficial abrasion, no active bleeding. Discharged back to festival.",
        )
    ]
    for e in encounters:
        db.add(e)
    db.flush()

    # 7. Incident Queue / Whiteboard
    incidents = [
        IncidentQueue(
            event_id=event.event_id,
            patient_id=patient_map["Pink hair"].patient_id,
            encounter_id=encounters[0].encounter_id,
            status="in_tent",
            assigned_to=staff_map["RN-1"].staff_id,
            location="medical_tent",
            priority="yellow",
            dispatch_time=datetime.utcnow(),
            radio_notes="Escalated to MD due to SSRI history. Active cooling running.",
        ),
        IncidentQueue(
            event_id=event.event_id,
            patient_id=patient_map["Male"].patient_id,
            encounter_id=encounters[1].encounter_id,
            status="observation",
            assigned_to=staff_map["Med-3"].staff_id,
            location="medical_tent",
            priority="yellow",
            dispatch_time=datetime.utcnow(),
            radio_notes="GHB coma. In recovery position, oxygen active.",
        ),
        IncidentQueue(
            event_id=event.event_id,
            patient_id=patient_map["Wristband #8832"].patient_id,
            status="dispatched",
            assigned_to=staff_map["Rover-2"].staff_id,
            location="stage_left",
            priority="red",
            dispatch_time=datetime.utcnow(),
            radio_notes="Unresponsive near stage left. Rover en route with Narcan.",
        ),
        IncidentQueue(
            event_id=event.event_id,
            patient_id=patient_map["Female"].patient_id,
            status="on_scene",
            assigned_to=staff_map["Rover-3"].staff_id,
            location="other",
            priority="green",
            dispatch_time=datetime.utcnow(),
            radio_notes="Anxiety/panic attack under influence. Rover sitting with patient.",
        ),
    ]
    for inc in incidents:
        db.add(inc)

    # 8. Reagent Test Log (requires disclaimer_agreed=True)
    reagent_log = ReagentLog(
        event_id=event.event_id,
        patient_id=patient_map["Pink hair"].patient_id,
        sample_description="Small pink pill with lightning bolt stamp",
        test_type="marquis",
        test_result="color_change_verified",
        color_observed="Fast Purple to Black",
        predicted_substance="MDMA presumptive",
        disclaimer_agreed=True,
        tester_staff_id=staff_map["Doc-1"].staff_id,
        created_at=datetime.utcnow(),
    )
    db.add(reagent_log)

    db.commit()
    print("Database seeding completed successfully.")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
