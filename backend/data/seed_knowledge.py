"""
Concert Med Ops — Bundled Seed Knowledge Base
==============================================

This script populates the RAG knowledge store with clinically accurate
content derived from public-domain and freely-available authoritative
sources.  It is designed to run in offline/air-gapped environments where
the full ingestion script (ingest_rag_sources.py) cannot reach the internet.

Run once to seed the DB:
    python -m backend.data.seed_knowledge

The full ingestion script will UPSERT over these entries when run with
actual downloaded PDFs, so running both is idempotent.

Sources:
  - SAMHSA Overdose Prevention and Response Toolkit (Public Domain, US Federal)
  - HHS CHEMM SALT/START Triage Algorithms (Public Domain, US Federal)
  - WHO Community Management of Opioid Overdose 2014 (CC BY-NC-SA 3.0 IGO)
  - CDC Opioid Overdose guidance (Public Domain, US Federal)
  - ACEP/clinical consensus on chemical sedation (paraphrase)
  - WMS Exercise-Associated Hyponatremia Guidelines (paraphrase/summary)
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_REPO_ROOT))

# ── Knowledge content ─────────────────────────────────────────────────────────

# Format: list of dicts with keys:
#   id, collection, text, title, source_url, condition_tags, drugs_tagged,
#   page_start (optional), section (optional)

SEED_CHUNKS = [

    # ── OPIOID OVERDOSE / NALOXONE ────────────────────────────────────────────

    {
        "id": "seed-opioid-001",
        "collection": "harm_reduction_protocols",
        "title": "SAMHSA Overdose Prevention and Response Toolkit (2024)",
        "source_url": "https://library.samhsa.gov/product/overdose-prevention-response-toolkit/pep23-03-00-001",
        "section": "Recognizing Opioid Overdose",
        "condition_tags": ["opioid_overdose"],
        "drugs_tagged": ["opioid", "fentanyl", "heroin"],
        "text": """RECOGNIZING AN OPIOID OVERDOSE
Signs and symptoms of opioid overdose: (1) Unresponsive or unconscious — does not respond to sternal rub or shouting their name. (2) Slow, shallow, or stopped breathing — fewer than one breath every 5 seconds, gurgling, or no breathing at all. (3) Choking or gurgling sounds. (4) Limp body. (5) Pale, blue, or cold skin, especially around lips and fingertips. (6) Pinpoint (very small) pupils. (7) Clammy or cool skin.

Distinguishing overdose from being "very high": A person who is very intoxicated can be roused — they respond to loud voices, sternal rub, or painful stimulus. A person in overdose cannot be woken up. If in doubt, treat as overdose.

High-potency opioids (fentanyl, carfentanil, nitazenes): May cause overdose faster, with less warning, and may require higher or repeated naloxone doses. Multiple 4 mg IN doses may be needed before response is seen. Do not assume no opioids because the person claims to have taken only stimulants — fentanyl contamination of non-opioid drug supplies is common.""",
    },

    {
        "id": "seed-opioid-002",
        "collection": "harm_reduction_protocols",
        "title": "SAMHSA Overdose Prevention and Response Toolkit (2024)",
        "source_url": "https://library.samhsa.gov/product/overdose-prevention-response-toolkit/pep23-03-00-001",
        "section": "Naloxone Administration",
        "condition_tags": ["opioid_overdose"],
        "drugs_tagged": ["naloxone", "opioid", "fentanyl", "nalmefene"],
        "text": """NALOXONE ADMINISTRATION PROTOCOL

Step 1 — Call 911 / activate EMS.

Step 2 — Try to stimulate: sternal rub, loud voice. If no response, administer naloxone.

Intranasal Naloxone (Narcan 4 mg/0.1 mL spray):
  • Insert nozzle into one nostril, press plunger firmly.
  • If no response in 2–3 minutes, administer second dose in other nostril.
  • Repeat every 2–3 minutes until response or EMS arrival.
  • For suspected fentanyl: start with 2 sprays (8 mg total) if available.

Intramuscular Naloxone (0.4 mg/mL vial):
  • Draw up 1 mL (0.4 mg). Inject into outer thigh or deltoid.
  • Repeat every 2–3 minutes if needed, up to 3–5 doses.

Onset of action: 2–5 minutes. Duration: 30–90 minutes (shorter than most opioids).

Post-reversal monitoring: Person may re-enter overdose as naloxone wears off. Monitor for minimum 2 hours. Do NOT leave alone. Repeat dosing may be required.

Xylazine (tranq) co-contamination: Naloxone does NOT reverse xylazine. Wounds, severe sedation, and bradycardia may persist. Provide airway support and transport. Skin wounds require wound care.""",
    },

    {
        "id": "seed-opioid-003",
        "collection": "harm_reduction_protocols",
        "title": "SAMHSA Overdose Prevention and Response Toolkit (2024)",
        "source_url": "https://library.samhsa.gov/product/overdose-prevention-response-toolkit/pep23-03-00-001",
        "section": "Rescue Breathing and Post-Overdose Care",
        "condition_tags": ["opioid_overdose"],
        "drugs_tagged": ["naloxone", "opioid"],
        "text": """RESCUE BREATHING DURING OPIOID OVERDOSE

If the person is not breathing or has fewer than 1 breath per 5 seconds:
1. Tilt head back, lift chin — open airway.
2. Pinch nose closed.
3. Give one breath every 5 seconds — watch chest rise.
4. Continue rescue breathing WHILE waiting for naloxone to take effect (2–5 min).
5. If BVM available, use it — provides better tidal volume than mouth-to-mouth.

Do not delay naloxone to establish airway — administer IN naloxone and then manage airway simultaneously.

POST-REVERSAL: Avoid giving water/food immediately — aspiration risk. If person is combative after naloxone, do NOT restrain forcefully — explain calmly that they are safe. The agitation is temporary.

Transport to ED indicated for: respiratory depression requiring >2 doses naloxone, suspected fentanyl analogue, xylazine co-exposure, coingestants (benzo + opioid), GCS not returning to baseline, chest pain, arrhythmia.""",
    },

    {
        "id": "seed-opioid-004",
        "collection": "harm_reduction_protocols",
        "title": "WHO Community Management of Opioid Overdose (2014)",
        "source_url": "https://www.ncbi.nlm.nih.gov/books/NBK264295/",
        "section": "Clinical Management Algorithm",
        "condition_tags": ["opioid_overdose"],
        "drugs_tagged": ["naloxone", "opioid", "heroin", "fentanyl"],
        "text": """WHO OPIOID OVERDOSE MANAGEMENT ALGORITHM (2014)

ASSESS: Unresponsive? Check AVPU — Alert, Voice, Pain, Unresponsive. GCS < 8 requires immediate airway management.

AIRWAY: Open with head-tilt chin-lift. Insert nasopharyngeal airway if available (28–32 Fr). Bag-valve-mask ventilation at 10–12 breaths/min if apneic.

BREATHING: SpO2 target ≥ 94%. Supplemental O2 at 15 L/min via non-rebreather mask if breathing but hypoxic.

CIRCULATION: Pulse check. If no pulse, initiate CPR. Opioid-induced PEA is reversible with naloxone — give IM/IV naloxone DURING CPR.

NALOXONE DOSE:
  Adult, known opioid overdose: 0.4 mg IV/IM; repeat q2–3 min; titrate to respiratory rate > 10/min.
  Adult, unknown mixed ingestion: start 0.1–0.2 mg IV to avoid acute withdrawal seizures in opioid-dependent patients.
  Pediatric: 0.01 mg/kg IV/IM; max 0.1 mg per dose.

GOAL: Restore adequate ventilation — NOT full consciousness. Over-reversal causes acute withdrawal and agitation that can be dangerous in festival environment.

DISPOSITION: All opioid overdoses requiring naloxone should be monitored ≥ 4 hours and transported to ED.""",
    },

    # ── MDMA / HEAT STROKE / HYPERTHERMIA ────────────────────────────────────

    {
        "id": "seed-heat-001",
        "collection": "harm_reduction_protocols",
        "title": "Festival Medical Protocol: Hyperthermia and Heat Stroke in MDMA Users",
        "source_url": "",
        "section": "Heat Stroke Recognition and Cooling",
        "condition_tags": ["heat_stroke", "rhabdomyolysis"],
        "drugs_tagged": ["mdma", "cocaine", "methamphetamine", "amphetamine"],
        "text": """HYPERTHERMIA & HEAT STROKE — FESTIVAL MEDICAL PROTOCOL

DEFINITIONS:
  Heat Exhaustion: Core temp < 40°C (104°F), normal mental status, heavy sweating. Can walk.
  Heat Stroke: Core temp ≥ 40°C (104°F) AND altered mental status (AMS) OR no sweating. Medical emergency.

MDMA-associated hyperthermia is the leading cause of MDMA-related death. MDMA impairs thermoregulation, causes intense physical activity (dancing), and increases metabolic heat production. Onset can be rapid.

RECOGNITION: Core temp ≥ 39°C (102.2°F) + any of: confusion, combativeness, seizure, syncope, diaphoresis ceasing in heat.

RECTAL TEMPERATURE IS THE GOLD STANDARD. Axillary and tympanic readings underestimate core temp by 1–2°C in hyperthermic patients.

COOLING PROTOCOL:
  TARGET: Reduce core temp to < 39°C within 30 minutes. Time-to-cool is the key prognostic factor.
  Step 1: Remove from heat, remove excess clothing.
  Step 2: Cold water immersion (ice bath / cold water tub) — most effective, reduces temp ~0.2°C/min.
  Step 3: If immersion unavailable: ice packs to neck, axillae, groin + large fans + spray mist evaporative cooling.
  Step 4: IV access — NS bolus 500 mL if hypotensive, avoid aggressive fluid resuscitation (risks hyponatremia).
  Step 5: Do NOT give antipyretics (acetaminophen, ibuprofen) — not effective for exertional heat stroke, may worsen hepatotoxicity.
  STOP COOLING at 39°C to prevent overshoot hypothermia.""",
    },

    {
        "id": "seed-heat-002",
        "collection": "harm_reduction_protocols",
        "title": "Festival Medical Protocol: Hyperthermia and Heat Stroke in MDMA Users",
        "source_url": "",
        "section": "Rhabdomyolysis and Complications",
        "condition_tags": ["heat_stroke", "rhabdomyolysis", "serotonin_syndrome"],
        "drugs_tagged": ["mdma", "cocaine", "methamphetamine"],
        "text": """COMPLICATIONS OF MDMA-RELATED HYPERTHERMIA

RHABDOMYOLYSIS: Near-universal in severe MDMA hyperthermia. CK > 1000 U/L on arrival; peaks at 24–48h. Dark urine (myoglobinuria) indicates severe rhabdo. Risk of acute renal failure. Treatment: aggressive IV fluid resuscitation (NS 200–300 mL/hr) targeting urine output 200–300 mL/hr. Avoid foley catheter delay — estimate output clinically. Transport all suspected rhabdo.

DIFFERENTIAL DIAGNOSIS — MDMA HYPERTHERMIA vs SEROTONIN SYNDROME:
  Serotonin Syndrome: rapid onset, clonus (rhythmic jerking), hyperreflexia, agitation. Temp usually < 41°C.
  Heat Stroke: high temp, AMS, no hyperreflexia. CK markedly elevated.
  Both can coexist with MDMA. Cool FIRST in either case.

SEIZURES: Benzodiazepines first-line (lorazepam 4 mg IV or diazepam 10 mg IV). Seizures worsen hyperthermia. May indicate hyponatremia (see EAH protocol). Check glucose.

AIRWAY: GCS ≤ 8 → RSI/intubation. Aspiration common. Position lateral if not intubated.

TRANSPORT THRESHOLD: Any of: core temp ≥ 40°C, AMS, seizure, dark urine, hypotension, GCS < 13. Call receiving ED before transport to activate cooling protocol.""",
    },

    # ── HYPONATREMIA / EAH ────────────────────────────────────────────────────

    {
        "id": "seed-eah-001",
        "collection": "harm_reduction_protocols",
        "title": "WMS Clinical Practice Guidelines for Exercise-Associated Hyponatremia (2020)",
        "source_url": "https://pubmed.ncbi.nlm.nih.gov/32044213/",
        "section": "EAH Diagnosis and Severity Classification",
        "condition_tags": ["hyponatremia"],
        "drugs_tagged": ["mdma"],
        "text": """EXERCISE-ASSOCIATED HYPONATREMIA (EAH) — WMS GUIDELINES 2020

DEFINITION: Serum sodium [Na+] < 135 mEq/L occurring during or within 24h of sustained physical activity.

FESTIVAL CONTEXT: MDMA causes SIADH (syndrome of inappropriate ADH secretion), causing water retention. Combined with excessive hypotonic fluid consumption and profuse sweating, rapid severe hyponatremia can develop. A patient may be seizing with sodium as low as 115–120 mEq/L within hours.

SEVERITY CLASSIFICATION (by symptoms, NOT sodium level):
  Mild-Moderate: Nausea, bloating, headache, vomiting. Conscious and ambulatory.
    → RESTRICT fluid intake. Oral hypertonic sodium (broth/electrolyte solution). Monitor closely.
  Severe (EAH Encephalopathy): Any of — seizure, unconsciousness, GCS < 14, respiratory distress, coma.
    → EMERGENCY: Administer IV 3% NaCl immediately. Do NOT delay for lab confirmation.

TREATMENT FOR SEVERE EAH (encephalopathy):
  3% NaCl 100 mL IV bolus over 10 minutes.
  Repeat twice at 10-minute intervals if no improvement (max 3 × 100 mL = 300 mL total).
  Goal: raise [Na+] by 4–6 mEq/L acutely to reduce cerebral edema.
  Do NOT give isotonic (0.9%) saline — will worsen hyponatremia.
  Do NOT restrict fluid if the patient is hypotensive — carefully titrate.

FIELD SODIUM MEASUREMENT: POC blood gas or i-STAT gives Na+ in minutes. A seizing patient with possible MDMA or excessive water intake should be presumed to have severe EAH until proven otherwise.""",
    },

    {
        "id": "seed-eah-002",
        "collection": "harm_reduction_protocols",
        "title": "WMS Clinical Practice Guidelines for Exercise-Associated Hyponatremia (2020)",
        "source_url": "https://pubmed.ncbi.nlm.nih.gov/32044213/",
        "section": "Differential Diagnosis and Transport",
        "condition_tags": ["hyponatremia"],
        "drugs_tagged": ["mdma"],
        "text": """EAH DIFFERENTIAL DIAGNOSIS AND TRANSPORT CRITERIA

EAH vs HEAT STROKE: Key differentiator — body temperature.
  Heat stroke: core temp ≥ 40°C, sweating often absent, CK very elevated.
  EAH: core temp often normal or mildly elevated, history of excessive fluid intake.
  Both can occur simultaneously — measure both sodium AND temperature.

EAH vs DRUG INTOXICATION: An MDMA user who is altered, seizing, or unconscious should be assessed for BOTH hyponatremia (excess water intake + SIADH) AND hyperthermia. Manage whichever is present first.

CRITICAL ERROR TO AVOID: Giving IV fluids (especially normal saline or D5W) to a hyponatremic patient who is seizing will worsen cerebral edema and cause herniation. Always check sodium before fluid resuscitation if possible.

TRANSPORT: Transport all patients with EAH encephalopathy (GCS < 14, seizure, unconsciousness) regardless of response to 3% NaCl bolus. Continue 3% NaCl infusion en route. Target Na+ correction: no more than 10–12 mEq/L per 24 hours total (to avoid osmotic demyelination syndrome — only relevant in hospital setting).

DISCHARGE CRITERIA (mild EAH only): Patient conscious, ambulatory, Na+ confirmed ≥ 130 mEq/L by POC test, symptoms resolved, able to take oral fluids. Minimum 2-hour post-treatment observation.""",
    },

    # ── GHB INTOXICATION ──────────────────────────────────────────────────────

    {
        "id": "seed-ghb-001",
        "collection": "harm_reduction_protocols",
        "title": "Festival Medical Protocol: GHB/GBL Intoxication Management",
        "source_url": "",
        "section": "GHB Overdose Recognition and Management",
        "condition_tags": ["ghb_intoxication"],
        "drugs_tagged": ["ghb", "gbl", "alcohol"],
        "text": """GHB / GBL INTOXICATION — FESTIVAL MEDICAL PROTOCOL

PHARMACOLOGY: GHB (gamma-hydroxybutyrate) and GBL (gamma-butyrolactone, a prodrug) cause rapid CNS and respiratory depression. GBL is more potent and faster onset. Steep dose-response curve — small dose increase can cause rapid transition from sedation to coma.

RECOGNITION:
  Mild: Euphoria, disinhibition, ataxia, mild sedation.
  Moderate: Confusion, slurred speech, vomiting (aspiration risk!), combativeness.
  Severe: Unconsciousness, airway loss, apnea, bradycardia, hypothermia.
  The "GHB coma": patient may appear dead — unresponsive, limp, minimal reflexes — then wake spontaneously within 1–6 hours. Do not assume brain death.

CRITICAL FEATURE: GHB has NO antidote. Management is entirely supportive.

AIRWAY MANAGEMENT:
  1. IMMEDIATE: Recovery position (left lateral decubitus) to prevent aspiration.
  2. Suction if vomiting. GHB increases vomiting risk significantly.
  3. Insert nasopharyngeal airway (NPA) if tolerated.
  4. BVM ventilation if apneic.
  5. RSI/intubation if: apnea persisting > 2 min, SpO2 < 92% on O2, unable to protect airway.

ALCOHOL CO-INGESTION: Dramatically worsens CNS and respiratory depression. Combined GHB + alcohol overdose has higher mortality. Lower threshold for airway intervention.

VITAL SIGN MONITORING: HR, BP, SpO2 every 5–10 min. Bradycardia (HR < 50) can occur — atropine 0.5 mg IV if symptomatic. Hypothermia (core temp < 35°C) common — apply warming blankets.""",
    },

    {
        "id": "seed-ghb-002",
        "collection": "harm_reduction_protocols",
        "title": "Festival Medical Protocol: GHB/GBL Intoxication Management",
        "source_url": "",
        "section": "GHB Monitoring and Disposition",
        "condition_tags": ["ghb_intoxication"],
        "drugs_tagged": ["ghb", "gbl", "alcohol"],
        "text": """GHB DISPOSITION AND MONITORING PROTOCOL

OBSERVATION PROTOCOL:
  Minimum 4-hour observation from estimated last dose.
  Neurological checks every 15 minutes: AVPU, pupil response, respiratory rate, SpO2.
  Do not leave unattended — sudden deterioration can occur, especially with polydrug ingestion.

PATIENT RECOVERY PATTERN: GHB typically clears rapidly (half-life ~30 min). Patients often awaken suddenly, confused and combative. Warning: rapid emergence can cause patient to abscond before adequate assessment. Ensure calm, supervised environment.

BENZODIAZEPINE CO-INGESTION: Do NOT give benzodiazepines for sedation — will worsen GHB CNS depression. If the patient becomes agitated on emergence, use verbal de-escalation. Physical restraint if patient at risk of self-harm, only as last resort.

RED FLAGS requiring immediate transport:
  • Apnea or SpO2 < 90% despite O2 and airway positioning.
  • Bradycardia < 40 with hypotension.
  • GCS ≤ 6 not improving after 30 min.
  • Suspected co-ingestion of multiple depressants.
  • Hyperthermia (separate heat stroke concern with stimulant co-use).
  • No improvement at 3 hours — consider alternate diagnosis.

WITHDRAWAL: GHB withdrawal (in heavy users) can include delirium, seizures, psychosis — appears 6–36h after last dose. Treat with benzodiazepines, consider ICU admission.""",
    },

    # ── SEROTONIN SYNDROME ────────────────────────────────────────────────────

    {
        "id": "seed-ss-001",
        "collection": "harm_reduction_protocols",
        "title": "Festival Medical Protocol: Serotonin Syndrome",
        "source_url": "",
        "section": "Hunter Criteria and Recognition",
        "condition_tags": ["serotonin_syndrome"],
        "drugs_tagged": ["mdma", "ssri", "maoi"],
        "text": """SEROTONIN SYNDROME — RECOGNITION AND HUNTER CRITERIA

DEFINITION: Life-threatening drug-induced excess serotonergic activity, causing the clinical triad of:
  1. Cognitive changes (agitation, confusion)
  2. Autonomic instability (diaphoresis, hyperthermia, tachycardia, hypertension)
  3. Neuromuscular abnormalities (clonus, hyperreflexia, tremor, ataxia)

HUNTER CRITERIA (requires serotonergic agent exposure PLUS):
  • Spontaneous clonus, OR
  • Inducible clonus + agitation or diaphoresis, OR
  • Ocular clonus + agitation or diaphoresis, OR
  • Tremor + hyperreflexia, OR
  • Hypertonia + fever > 38°C + ocular or inducible clonus
  Sensitivity 84%, specificity 97% for serotonin syndrome.

FESTIVAL TRIGGERS: MDMA alone (serotonin-releasing), MDMA + SSRI/SNRI (most common), MDMA + MAOI (life-threatening — extreme hyperthermia), cocaine + MAOI.

KEY DIFFERENTIATORS:
  vs Heat Stroke: clonus and hyperreflexia ABSENT in heat stroke.
  vs NMS (Neuroleptic Malignant Syndrome): NMS onset over days, "lead-pipe" rigidity, bradykinesia. Serotonin syndrome onset within hours, hyperreflexia, clonus.
  vs Anticholinergic syndrome: anticholinergic = dry skin/mucosa, urinary retention; serotonin syndrome = diaphoresis.

TEMPERATURE IN SS: Mild-moderate SS: temp < 39°C. Severe SS: temp > 41°C is an emergency — active cooling required as for heat stroke.""",
    },

    {
        "id": "seed-ss-002",
        "collection": "harm_reduction_protocols",
        "title": "Festival Medical Protocol: Serotonin Syndrome",
        "source_url": "",
        "section": "Treatment and Disposition",
        "condition_tags": ["serotonin_syndrome"],
        "drugs_tagged": ["mdma", "ssri", "maoi", "benzodiazepines"],
        "text": """SEROTONIN SYNDROME — TREATMENT PROTOCOL

DISCONTINUE PRECIPITATING AGENT(S): Remove any transdermal patches, ensure no further drug intake.

MILD-MODERATE SS (temp < 39°C, intact airway, no seizures):
  1. Benzodiazepines: Diazepam 5–10 mg IV (or lorazepam 2 mg IV) — first-line for agitation and neuromuscular hyperactivity. Repeat q5–10 min, titrate to effect.
  2. Cyproheptadine (5-HT2A antagonist): 12 mg PO loading dose, then 2 mg q2h if tolerated. Useful adjunct for mild-moderate SS. NOT available IV.
  3. Cooling measures: Fans, cool IV fluids. Antipyretics NOT effective.
  4. Supportive: IV fluid resuscitation for diaphoresis losses. O2 supplementation.

SEVERE SS (temp ≥ 39°C, seizures, rigidity, GCS < 13):
  1. Active cooling: Ice packs axillae/groin + fan evaporative (same as heat stroke).
  2. High-dose benzodiazepines: Diazepam 10–20 mg IV, repeat aggressively.
  3. Airway: RSI/intubation for airway protection if GCS ≤ 8.
  4. AVOID: Succinylcholine for RSI if rigidity/rhabdomyolysis suspected — use rocuronium.
  5. Transport ALL severe SS to ICU-capable facility.

MAOI + MDMA (or MAOI + other serotonergic): Extreme risk. Can produce temp > 43°C within minutes. Highest priority transport. Consider giving chlorpromazine 50 mg IM if MAOI-serotonin crisis.""",
    },

    # ── AGITATION / CHEMICAL SEDATION ────────────────────────────────────────

    {
        "id": "seed-agit-001",
        "collection": "harm_reduction_protocols",
        "title": "ACEP Clinical Policy: Hyperactive Delirium with Severe Agitation (2021) — Summary",
        "source_url": "https://www.acep.org/siteassets/new-pdfs/clinical-policies/severe-agitation-cp.pdf",
        "section": "Chemical Sedation Algorithm",
        "condition_tags": ["agitation"],
        "drugs_tagged": ["mdma", "cocaine", "methamphetamine", "benzodiazepines", "ketamine"],
        "text": """HYPERACTIVE DELIRIUM / SEVERE AGITATION — FESTIVAL PROTOCOL

SAFETY FIRST: Severe agitation with sympathomimetic toxicity (stimulant overdose, heat stroke) is a medical emergency, not a behavioral one. Restraint alone increases risk of death from hyperthermia, acidosis, rhabdomyolysis.

VERBAL DE-ESCALATION: Always attempt first (30–60 seconds). Calm, quiet environment, one-on-one approach, remove stimuli.

CHEMICAL SEDATION — PREFERRED AGENTS (ACEP 2021 guideline):

Option 1 — Benzodiazepines (first-line for stimulant toxicity):
  Midazolam 5–10 mg IM (preferred for rapid IM onset, ~3–5 min).
  Lorazepam 2–4 mg IM (alternative).
  Diazepam 5–10 mg IV.

Option 2 — Droperidol 5–10 mg IM/IV (second-line, effective, QTc risk — needs ECG).

Option 3 — Ketamine 4–5 mg/kg IM or 1–2 mg/kg IV:
  Rapid, titratable, preserves airway reflexes.
  Risk: emergence agitation, laryngospasm (rare). Airway equipment MUST be present.
  Does NOT worsen cocaine- or stimulant-induced hypertension as much as physical restraint.

AVOID: Haloperidol alone in hyperthermia (may lower seizure threshold, impairs thermoregulation). Olanzapine + benzodiazepines simultaneously (respiratory depression risk).

AFTER SEDATION: Monitor airway, respiratory rate, SpO2 continuously. Temperature check q10 min.""",
    },

    {
        "id": "seed-agit-002",
        "collection": "harm_reduction_protocols",
        "title": "ACMT Position Statement: End the Use of 'Excited Delirium' (2023) — Summary",
        "source_url": "https://www.acmt.net/wp-content/uploads/2023/05/PS_230501_End-the-Use-of-the-Term-Excited-Delirium.pdf",
        "section": "Acute Behavioral Disturbance Framework",
        "condition_tags": ["agitation"],
        "drugs_tagged": ["cocaine", "methamphetamine", "mdma"],
        "text": """ACMT 2023: ACUTE BEHAVIORAL DISTURBANCE (replaces "Excited Delirium")

ACMT has formally retired the term "excited delirium" as it lacks clinical validity, has been used to justify harmful restraint practices, and disproportionately affects Black and Indigenous individuals.

PREFERRED TERMINOLOGY: "Acute Behavioral Disturbance" (ABD) or "Sympathomimetic Toxicity with Agitation."

CLINICAL PRESENTATION: Tachycardia, hyperthermia, diaphoresis, extreme agitation, disorganized behavior, superhuman strength, impaired pain response. Can be caused by: stimulant toxicity (cocaine, methamphetamine, MDMA), acute psychosis, traumatic brain injury, hypoxia, hypoglycemia.

RESTRAINT GUIDELINES:
  • Physical restraint (especially prone/facedown) increases mortality — causes positional asphyxia.
  • If restraint is required, it must be SUPINE or lateral, NEVER prone.
  • Minimize duration of physical restraint — chemical sedation is the priority.
  • Hobble restraints (tying ankles to wrists behind back) are CONTRAINDICATED.

MONITORING DURING RESTRAINT: SpO2, HR, RR, mental status every 2 minutes. Any deterioration: release restraint, reassess airway immediately.

DIFFERENTIAL: Always check glucose (hypoglycemia), SpO2 (hypoxia), temperature (hyperthermia) before attributing ABD to drug toxicity alone.""",
    },

    # ── TRIAGE ALGORITHMS ─────────────────────────────────────────────────────

    {
        "id": "seed-triage-001",
        "collection": "mass_gathering_protocols",
        "title": "HHS CHEMM: START Adult Triage Algorithm",
        "source_url": "https://chemm.hhs.gov/startadult.htm",
        "section": "START Triage Steps",
        "condition_tags": ["triage_mci"],
        "drugs_tagged": [],
        "text": """START (SIMPLE TRIAGE AND RAPID TREATMENT) ADULT TRIAGE ALGORITHM
Source: HHS CHEMM — Public Domain (US Federal)

START triage is performed in 30 seconds per patient. Used in mass casualty incidents (MCI).

STEP 1 — WALKING:
  Can patient walk? YES → Tag GREEN (Minor). Move to secondary collection point.
  NO → Stay and assess further.

STEP 2 — RESPIRATIONS:
  Is patient breathing? NO → Open airway (head-tilt chin-lift). Now breathing? YES → Tag RED (Immediate).
  Still not breathing → Tag BLACK (Expectant/Deceased).
  Breathing rate > 30/min → Tag RED (Immediate).
  Breathing rate ≤ 30/min → Continue to Step 3.

STEP 3 — PERFUSION (Radial pulse or capillary refill):
  No radial pulse OR capillary refill > 2 seconds → Tag RED (Immediate). Control major bleeding.
  Radial pulse present AND capillary refill ≤ 2 seconds → Continue to Step 4.

STEP 4 — MENTAL STATUS:
  Can follow simple commands? YES → Tag YELLOW (Delayed).
  Cannot follow commands → Tag RED (Immediate).

TRIAGE TAGS:
  RED (Immediate): Life-threatening, survivable with immediate care. First priority.
  YELLOW (Delayed): Serious, stable. Can wait 30–60 min without life threat.
  GREEN (Minor): Minor injuries. "Walking wounded."
  BLACK (Expectant): Deceased or unsurvivable given current resources.

Re-triage: Patient status can change — re-assess RED and YELLOW patients at regular intervals.""",
    },

    {
        "id": "seed-triage-002",
        "collection": "mass_gathering_protocols",
        "title": "HHS CHEMM: SALT Mass-Casualty Triage Algorithm",
        "source_url": "https://chemm.hhs.gov/salttriage.htm",
        "section": "SALT Triage Steps",
        "condition_tags": ["triage_mci"],
        "drugs_tagged": [],
        "text": """SALT (SORT, ASSESS, LIFESAVING INTERVENTIONS, TREATMENT/TRANSPORT) TRIAGE ALGORITHM
Source: HHS CHEMM — Public Domain (US Federal)

SALT is a national standard MCI triage algorithm; incorporates limited lifesaving interventions before categorization.

STEP 1 — SORT (Global Assessment):
  Ask: "If you can walk, move to [designated area] NOW." → Walking patients = potential GREEN.
  Ask remaining non-walkers: "Wave your hand/feet if you can hear me." → Minimal movement = YELLOW priority.
  Still, silent patients with no movement → Assess FIRST (potential RED).

STEP 2 — ASSESS (Individual assessment in priority order: still > minimal movement > walkers):
  Perform lifesaving interventions (LSI) immediately if needed:
    • Control major bleeding (tourniquet, direct pressure).
    • Open airway (positioning, NPA — do NOT intubate during primary triage).
    • 2–3 rescue breaths for pediatric apneic patient (adult apneic = EXPECTANT in MCI).
    • Decompress tension pneumothorax (needle decompression).
    • Auto-injector antidote (CBRN context).

STEP 3 — CATEGORIZE (after LSI):
  IMMEDIATE (RED): Immediate threat to life. Likely to survive with available resources.
  DELAYED (YELLOW): Serious injury, can wait.
  MINIMAL (GREEN): Minor injury, can self-assist.
  EXPECTANT (BLACK/GRAY): Unlikely to survive given resources; or deceased.

SALT advantage over START: permits brief LSIs before tagging; applicable to pediatric patients.""",
    },

    {
        "id": "seed-triage-003",
        "collection": "mass_gathering_protocols",
        "title": "WHO Public Health for Mass Gatherings: Key Considerations (2015)",
        "source_url": "https://iris.who.int/handle/10665/162109",
        "section": "Medical Planning for Mass Gatherings",
        "condition_tags": ["mass_gathering_ops", "triage_mci", "transport"],
        "drugs_tagged": [],
        "text": """WHO MASS GATHERING MEDICAL PLANNING — KEY METRICS (2015)

MEDICAL RESOURCE ESTIMATION:
  Festival patient presentation rate: 0.5–5% of attendance per day (varies by event type, alcohol availability, temperature).
  For EDM/rave events with drug use: expect 1–3% per day, with up to 10–15% requiring assessment.
  Requiring transport to hospital: typically 0.1–0.5% of attendance.

TRIAGE AREA SETUP:
  Primary triage point: near main entrance/exits, ambulance access.
  Treatment areas: separated by triage level. RED area must have airway equipment, crash cart, O2.
  Capacity trigger: pre-define the patient census that triggers MCI protocol and requests additional resources.

MEDICAL STAFF RATIOS (WHO recommendation for moderate-risk events):
  1 physician per 1,000–2,000 attendees.
  1 nurse or paramedic per 500–1,000 attendees.
  1 first responder per 250–500 attendees.
  At least 2 BLS ambulances on-site at events > 5,000 attendees.

COMMAND STRUCTURE:
  Medical Director: responsible for all clinical decisions, liaison with EMS command.
  Incident Commander: overall event coordination, activates MCI plan.
  Medical Coordinator: manages patient flow, transport requests, hospital communication.

HOSPITAL DIVERSION MONITORING: Establish radio/phone contact with receiving hospitals before event starts. Identify Level I trauma center, nearest ED with toxicology capability. Establish helicopter landing zone if needed.""",
    },

    {
        "id": "seed-triage-004",
        "collection": "mass_gathering_protocols",
        "title": "WHO Public Health for Mass Gatherings: Key Considerations (2015)",
        "source_url": "https://iris.who.int/handle/10665/162109",
        "section": "Drug and Alcohol Medical Response at Mass Gatherings",
        "condition_tags": ["mass_gathering_ops", "harm_reduction", "opioid_overdose"],
        "drugs_tagged": ["mdma", "alcohol", "opioid", "ghb"],
        "text": """WHO MASS GATHERING: DRUG AND ALCOHOL MEDICAL RESPONSE

SUBSTANCE USE PREVALENCE AT MUSIC FESTIVALS: Alcohol (60–80%), cannabis (20–30%), MDMA/ecstasy (15–25%), stimulants (5–15%), GHB (2–8%), opioids (1–5%). Polysubstance use is the norm, not the exception.

HARM REDUCTION SERVICES (recommended by WHO):
  Drug-checking services: Reagent testing, FTIR spectrometry allows substance identification. Reduces accidental fentanyl ingestion.
  Medical outreach: Mobile units/roaming medics in crowd reduce time to first assessment.
  Chill-out zones: Quiet, cool areas for patients who are overwhelmed or intoxicated but stable.
  Safe messaging: "If you choose to use, don't use alone; stay hydrated but don't overdrink water."

MEDICAL ENCOUNTER DOCUMENTATION: Record substance(s) reported for each encounter. Track temporal patterns (overdose clustering suggests contaminated batch). Alert on-site harm reduction team if cluster identified.

HYDRATION GUIDANCE FOR MDMA USERS: Encourage 500 mL/hour during dance activity (not more — hyponatremia risk). Electrolyte drinks preferred over plain water. Rest breaks mandatory if core temp elevated.

TEMPERATURE MONITORING: In-crowd medical teams with thermometers. Any person found collapsed/unresponsive: rectal temperature mandatory. Triage tent should have a dedicated cooling area with ice/cold water availability.""",
    },

    # ── AMA / CAPACITY ASSESSMENT ─────────────────────────────────────────────

    {
        "id": "seed-ama-001",
        "collection": "harm_reduction_protocols",
        "title": "Festival Medical Protocol: Against Medical Advice (AMA) and Capacity Assessment",
        "source_url": "",
        "section": "Capacity Checklist and AMA Documentation",
        "condition_tags": ["transport"],
        "drugs_tagged": [],
        "text": """AMA REFUSAL AND CAPACITY ASSESSMENT — FESTIVAL MEDICAL

WHEN A PATIENT REFUSES TRANSPORT OR TREATMENT:
  Assess decision-making capacity before accepting refusal.

CAPACITY CHECKLIST (all 4 required):
  1. UNDERSTAND: Can the patient articulate the medical condition, proposed treatment, and alternatives?
  2. APPRECIATE: Does the patient acknowledge this applies to them (not abstract)?
  3. REASON: Can the patient provide rational reasons for refusal (consistent with their values)?
  4. COMMUNICATE: Can the patient clearly and consistently express their choice?

CAPACITY IS IMPAIRED BY: Active intoxication, severe agitation, GCS < 15, confusion, dissociation, active psychosis. A patient who cannot pass the 4-part test LACKS capacity — treat and transport.

AMA DOCUMENTATION:
  Document: patient's stated reason for refusal, capacity assessment findings, medical risks explained, alternatives offered (including supervised observation, calling a friend to sit with them).
  Witness signature strongly encouraged.
  Do NOT abandon a patient who lacks capacity — continue to provide available care.

MINORS: Persons < 18 years cannot consent to refuse life-saving care. Medical director authority to treat applies. Attempt to contact parent/guardian but do not delay treatment.

GOOD SAMARITAN LAWS: In most US states, individuals who call for help for an overdose victim have protection from prosecution. Inform patients this protection exists — reduces reluctance to seek help.""",
    },

    # ── SUBSTANCE DATABASE ────────────────────────────────────────────────────

    {
        "id": "seed-sub-001",
        "collection": "substance_database",
        "title": "Substance Profile: MDMA (Ecstasy, Molly)",
        "source_url": "",
        "section": "Pharmacology and Clinical Effects",
        "condition_tags": ["heat_stroke", "hyponatremia", "serotonin_syndrome"],
        "drugs_tagged": ["mdma", "ssri"],
        "text": """SUBSTANCE PROFILE: MDMA (Ecstasy, Molly, E, X)

PHARMACOLOGY: MDMA (3,4-methylenedioxymethamphetamine) — entactogen/stimulant.
  • Mechanism: Releases serotonin (>dopamine >norepinephrine) from presynaptic vesicles; blocks reuptake.
  • Typical dose: 75–150 mg orally. Street pills vary widely (50–300+ mg, may contain adulterants).
  • Onset: 30–60 min oral. Peak: 1.5–3 hours. Duration: 3–5 hours.
  • Common adulterants: methamphetamine, amphetamine, bath salts, fentanyl (rare but documented).

CLINICAL EFFECTS (therapeutic doses): Euphoria, empathy, increased sociability, mild stimulation, mild tachycardia.

TOXIC EFFECTS (overdose/hot environment):
  • Hyperthermia: MOST DANGEROUS. Core temp > 42°C possible. Cooling is life-saving.
  • SIADH: Causes water retention → hyponatremia, especially with excessive plain water consumption.
  • Serotonin syndrome: Especially with SSRIs or MAOIs.
  • Cardiac: Tachycardia, hypertension, rarely arrhythmia.
  • Rhabdomyolysis: Common with severe hyperthermia.

DRUG INTERACTIONS (danger level HIGH):
  • MDMA + MAOI: CONTRAINDICATED. Serotonin crisis, extreme hyperthermia, death.
  • MDMA + SSRI/SNRI: Increased serotonin syndrome risk.
  • MDMA + lithium: Seizure risk.
  • MDMA + alcohol: Masks dehydration, compound cardiac stress.
  • MDMA + GHB: Unpredictable CNS effects, crash risk as GHB wears off.

REAGENT TEST: Marquis reagent → purple-to-black = positive for MDMA/MDA.""",
    },

    {
        "id": "seed-sub-002",
        "collection": "substance_database",
        "title": "Substance Profile: Fentanyl and High-Potency Opioids",
        "source_url": "",
        "section": "Fentanyl Overdose and Naloxone Dosing",
        "condition_tags": ["opioid_overdose"],
        "drugs_tagged": ["fentanyl", "opioid", "naloxone", "xylazine"],
        "text": """SUBSTANCE PROFILE: FENTANYL AND HIGH-POTENCY SYNTHETIC OPIOIDS

PHARMACOLOGY: Fentanyl is 50–100× more potent than morphine by weight. Carfentanil is 100× more potent than fentanyl. Nitazenes (isotonitazene, metonitazene) emerging, extreme potency.

STREET PRESENCE: Fentanyl is found in counterfeit opioid pills (M30 "blues"), heroin, cocaine, and increasingly MDMA and other street drugs. Cannot be detected by sight, smell, or taste.

OVERDOSE PRESENTATION: Rapid unconsciousness, apnea, pinpoint pupils, cyanosis, bradycardia. May appear "dead" within seconds of IV use. Transdermal/intranasal absorption can delay presentation.

NALOXONE DOSING FOR FENTANYL:
  Standard naloxone 0.4 mg may be INSUFFICIENT for fentanyl overdose.
  Start with 4 mg intranasal (one full Narcan spray per nostril simultaneously if possible).
  Repeat 4 mg q2–3 min until response. Some cases require 10–20 mg total.
  High-dose naloxone autoinjectors (2 mg IM, Zimhi) available for first responders.

XYLAZINE CO-CONTAMINATION ("tranq dope"):
  Xylazine is a veterinary alpha-2 agonist increasingly found mixed with fentanyl.
  Naloxone does NOT reverse xylazine effects.
  Wounds: xylazine causes severe necrotic wounds at injection sites.
  Management: naloxone for the opioid component + airway/breathing support for xylazine.

DURATION MISMATCH: Fentanyl duration ≈ 30–60 min, shorter than many naloxone formulations. Re-narcotization risk is LOWER than heroin (where naloxone wears off before opioid). But repeated dosing may still be needed.""",
    },

    {
        "id": "seed-sub-003",
        "collection": "substance_database",
        "title": "Substance Profile: GHB and GBL",
        "source_url": "",
        "section": "GHB Pharmacology and Toxicology",
        "condition_tags": ["ghb_intoxication"],
        "drugs_tagged": ["ghb", "gbl", "alcohol"],
        "text": """SUBSTANCE PROFILE: GHB (Gamma-Hydroxybutyrate) / GBL (Gamma-Butyrolactone)

PHARMACOLOGY:
  GHB: Endogenous CNS neurotransmitter; GABA-B agonist, GHB receptor agonist.
  GBL: Prodrug — converted to GHB in the body. More lipid-soluble, faster onset, higher potency per mL.
  Common forms: liquid (salty/soapy taste), capsules, powder. Typical "cap" = 1–2 mL GBL liquid.

DOSE-RESPONSE CURVE — EXTREMELY STEEP:
  1 mL GBL = mild sedation/euphoria.
  1.5–2 mL GBL = sedation, ataxia, amnesia.
  2–3 mL GBL = unconsciousness.
  Small additional dose can cause rapid transition from social to comatose.

TIMELINE:
  Onset: 15–30 min oral. Peak: 30–60 min. Duration: 1.5–3 hours (GHB); slightly shorter for GBL.
  Elimination: 95% eliminated in 4 hours. Blood/urine tests negative within 8–12 hours.

INTERACTIONS:
  GHB + Alcohol: DANGEROUS — synergistic CNS and respiratory depression.
  GHB + Benzodiazepines: Enhanced sedation — avoid giving benzos for sedation.
  GHB + Opioids: Respiratory depression risk.
  GHB + MDMA: "G-drop" — crash when GHB wears off while MDMA stimulant effects wane.

REAGENT TEST: GHB has no color reaction on standard reagents — cannot be field-tested by standard methods. GHB test strips available (specific for GHB in drinks).""",
    },

    {
        "id": "seed-sub-004",
        "collection": "substance_database",
        "title": "Substance Profile: Ketamine",
        "source_url": "",
        "section": "Ketamine Toxicology and Clinical Use",
        "condition_tags": ["agitation"],
        "drugs_tagged": ["ketamine", "alcohol"],
        "text": """SUBSTANCE PROFILE: KETAMINE (Special K, Vitamin K, Ket)

PHARMACOLOGY: NMDA receptor antagonist. Dissociative anesthetic. Also used clinically for procedural sedation and chemical sedation of agitated patients.

RECREATIONAL USE: Insufflated (snorted), rarely IV. "K-hole" = profound dissociative state at high doses. Typical recreational dose: 50–150 mg intranasal. Anesthetic dose: 1–2 mg/kg IV or 4–6 mg/kg IM.

CLINICAL EFFECTS AT RECREATIONAL DOSES:
  Low dose: Mild dissociation, analgesia, euphoria.
  High dose (K-hole): Profound dissociation, inability to move/speak, amnesia, preserved airway reflexes (usually).

OVERDOSE PRESENTATION: Deep dissociation, ataxia, slurred speech. Respiratory depression is rare with intranasal use. Vomiting is common — aspiration risk. Laryngospasm rare but possible.

MANAGEMENT: Lateral recovery position. Monitor SpO2. Stimulus reduction (quiet, dark). Most cases resolve in 30–90 min.

AIRWAY ALERT: While ketamine is known for "airway protection," high doses (especially IV or combined with alcohol/opioids) can cause apnea. Have BVM ready.

EMERGENCY CLINICAL USE AT FESTIVALS: Ketamine 4–5 mg/kg IM is guideline-recommended for severe agitation in suspected stimulant toxicity. Provides rapid (3–5 min), titratable sedation. Requires airway monitoring post-administration.

BLADDER: Chronic heavy use causes ketamine cystitis/uropathy — not acute concern at festival.""",
    },

    {
        "id": "seed-sub-005",
        "collection": "substance_database",
        "title": "Substance Interactions: High-Risk Polysubstance Combinations",
        "source_url": "",
        "section": "Dangerous Drug Combinations at Festivals",
        "condition_tags": ["opioid_overdose", "serotonin_syndrome", "ghb_intoxication"],
        "drugs_tagged": ["mdma", "ghb", "alcohol", "opioid", "ssri", "maoi", "benzodiazepines"],
        "text": """HIGH-RISK POLYSUBSTANCE COMBINATIONS — FESTIVAL CONTEXT

DANGER LEVEL: EXTREME (requires immediate medical attention)

1. MDMA + MAOI (monoamine oxidase inhibitor — e.g., phenelzine, selegiline, Syrian rue, harmala alkaloids in ayahuasca):
   Mechanism: MAOIs prevent serotonin breakdown → extreme serotonin accumulation with MDMA's release.
   Effects: Serotonin crisis, hyperthermia > 42°C, seizures, cardiovascular collapse.
   Treatment: Aggressive cooling, high-dose benzodiazepines, cyproheptadine, ICU. Chlorpromazine 50 mg IM if available.

2. GHB + Alcohol (any dose):
   Mechanism: Additive CNS and respiratory depression.
   Effects: Respiratory arrest from doses that would be safe individually. No antidote.
   Treatment: Airway management, supportive care. Transport.

3. Opioid + Benzodiazepine (Benzo + Opioid):
   Mechanism: Synergistic respiratory depression.
   Effects: Naloxone reverses opioid component but not benzo — partial response to naloxone common.
   Treatment: Naloxone + airway support. Flumazenil for benzos only if benzo is known and no seizure history.

4. Stimulant (MDMA/cocaine) + MDMA: Additive cardiac stress, hyperthermia.

5. Multiple Depressants (GHB + Opioid + Alcohol): Respiratory arrest risk extremely high.

HARM REDUCTION MESSAGE: "No drug is safe in combination with multiple depressants. GHB + alcohol is particularly dangerous even at low doses of each."

PATTERN RECOGNITION: If multiple patients present with similar symptoms in a short time frame (30–60 min), suspect contaminated batch — activate medical director notification protocol.""",
    },
]


# ── Ingestion logic ───────────────────────────────────────────────────────────

def seed_knowledge_base(engine=None, dry_run: bool = False) -> None:
    """Write all SEED_CHUNKS into the RAG knowledge store.

    Accepts an existing engine instance to avoid circular imports when called
    from RAGEngine._bootstrap_from_kb.  Creates a new engine if none given.
    """
    if engine is None:
        from backend.ai.rag_engine import RAGEngine
        engine = RAGEngine()

    by_collection: dict[str, list] = {}
    for chunk in SEED_CHUNKS:
        col = chunk["collection"]
        by_collection.setdefault(col, []).append(chunk)

    total_written = 0
    for collection, chunks in by_collection.items():
        docs = [c["text"] for c in chunks]
        ids = [c["id"] for c in chunks]
        metadatas = [
            {
                "title": c["title"],
                "source_url": c.get("source_url", ""),
                "section": c.get("section", ""),
                "condition_tags": c.get("condition_tags", []),
                "drugs_tagged": c.get("drugs_tagged", []),
                **({"page_start": c["page_start"], "page_end": c["page_end"]}
                   if c.get("page_start") is not None else {}),
            }
            for c in chunks
        ]
        if dry_run:
            print(f"  [DRY RUN] Would write {len(chunks)} chunks → {collection}")
        else:
            engine.add_documents(
                collection_name=collection,
                documents=docs,
                metadatas=metadatas,
                ids=ids,
            )
            print(f"  ✓ {len(chunks)} chunks → {collection}")
        total_written += len(chunks)

    if not dry_run:
        stats = engine.all_collection_stats()
        print(f"\nKnowledge store totals:")
        for col, cnt in sorted(stats.items()):
            print(f"  {col:<40} {cnt:>5} chunks")

    print(f"\nSeed complete: {total_written} chunks{'(dry run)' if dry_run else ' written'}.")


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Seed the RAG knowledge store with bundled clinical content.")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()
    print("Concert Med Ops — Seeding knowledge base...")
    seed_knowledge_base(dry_run=args.dry_run)
