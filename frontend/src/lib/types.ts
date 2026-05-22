export interface Event {
  event_id: string;
  name: string;
  venue?: string;
  date_start?: string;
  date_end?: string;
  expected_attendance?: number;
  medical_lead?: string;
  contact_info?: string;
  weather_high_f?: number;
  weather_humidity?: number;
  notes?: string;
  created_at?: string;
}

export interface StaffMember {
  staff_id: string;
  event_id: string;
  name: string;
  role: "emt" | "paramedic" | "rn" | "md" | "supervisor";
  call_sign: string;
  is_on_shift: boolean;
  created_at?: string;
}

export interface VitalSigns {
  hr?: number;
  bp?: string;
  temp_f?: number;
  spo2?: number;
  rr?: number;
  gcs?: number;
  pupils?: string;
  skin_condition?: string;
}

export interface SubstanceReported {
  name: string;
  route?: string;
  time_taken?: string;
  amount?: string;
}

export interface Patient {
  patient_id: string;
  event_id: string;
  identifier: string; // wristband # or physical description
  approx_age?: number;
  gender?: string;
  weight_kg?: number;
  known_allergies: string[];
  known_medications: string[];
  known_conditions: string[];
  substances_reported: SubstanceReported[];
  location_found: "venue_tent" | "campground" | "gate" | "field" | "other";
  is_active: boolean;
  created_at?: string;
}

export interface Intervention {
  action: string;
  time?: string;
  by_whom?: string;
  notes?: string;
}

export interface Encounter {
  encounter_id: string;
  event_id: string;
  patient_id: string;
  doc_type: "pcr" | "otc";
  logged_by: string; // staff_id
  encounter_time: string;
  chief_complaint?: string;
  symptoms: string[];
  vital_signs: VitalSigns;
  substances_involved: string[];
  triage_level: "green" | "yellow" | "red" | "black";
  escalated_to?: string; // staff_id
  escalation_time?: string;
  interventions: Intervention[];
  disposition: "released" | "observation" | "transport" | "ama" | "deceased";
  transport_hospital?: string;
  transport_unit?: string;
  transport_time?: string;
  ama_documented: boolean;
  ama_capacity_assessment?: string;
  ai_response?: string;
  ai_model_used?: string;
  photo_paths: string[];
  notes?: string;
  created_at?: string;
}

export interface IncidentQueue {
  incident_id: string;
  event_id: string;
  patient_id: string;
  encounter_id?: string;
  status: "dispatched" | "en_route" | "on_scene" | "in_tent" | "observation" | "cleared";
  assigned_to: string; // staff_id
  location: string;
  priority: "green" | "yellow" | "red" | "black";
  dispatch_time: string;
  arrival_time?: string;
  cleared_time?: string;
  radio_notes?: string;
  created_at?: string;
  patient?: Patient;
  assigned_staff?: StaffMember;
}

export interface HospitalDirectory {
  hospital_id: string;
  name: string;
  distance_miles?: number;
  drive_time_min?: number;
  trauma_level?: number;
  capabilities: string[];
  phone?: string;
  address?: string;
  is_on_diversion: boolean;
  notes?: string;
}

export interface ReagentLog {
  log_id: string;
  event_id: string;
  patient_id?: string;
  sample_description: string;
  test_type: "fent_strip" | "marquis" | "mecke" | "mandelin" | "folin" | "ehhrlich" | "ftir";
  test_result: "positive" | "negative" | "color_change_verified" | "inconclusive";
  color_observed?: string;
  predicted_substance?: string;
  disclaimer_agreed: boolean;
  tester_staff_id: string;
  created_at?: string;
}

export interface Supply {
  supply_id: string;
  event_id: string;
  name: string;
  category: "medication" | "equipment" | "ppe" | "narcan" | "iv_fluid" | "reagent";
  quantity_start: number;
  quantity_used: number;
  quantity_remaining: number;
  expiration_date?: string;
  lot_number?: string;
  location: "venue_tent" | "campground" | "rover_kit";
  notes?: string;
}
