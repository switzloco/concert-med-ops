"""
Concert Med Ops — Unsloth Fine-Tune Training Data Generator
===========================================================

Converts backend/data/harm_reduction_kb.json + prompt_templates.py into
a JSONL dataset in ShareGPT conversation format ready for Unsloth SFTTrainer.

Usage:
    python notebooks/generate_training_data.py
    python notebooks/generate_training_data.py --output custom/path/dataset.jsonl
    python notebooks/generate_training_data.py --format alpaca   # alternate format

Output format: ShareGPT (default) or Alpaca
  ShareGPT: {"conversations": [{"from": "system", ...}, {"from": "human", ...}, {"from": "gpt", ...}]}
  Alpaca:   {"instruction": "...", "input": "...", "output": "..."}

References:
  - Unsloth dataset format guide: https://docs.unsloth.ai/basics/datasets-guide
  - ShareGPT format spec: https://docs.unsloth.ai/basics/datasets-guide#conversational
  - SFTTrainer docs: https://huggingface.co/docs/trl/sft_trainer
  - Unsloth GitHub examples: https://github.com/unslothai/unsloth-zoo/tree/main/notebooks
"""

import argparse
import json
import pathlib
import random
import re
import sys
from typing import Any

# ── Paths ────────────────────────────────────────────────────────────────────

REPO_ROOT = pathlib.Path(__file__).parent.parent
KB_PATH = REPO_ROOT / "backend" / "data" / "harm_reduction_kb.json"
DEFAULT_OUTPUT = pathlib.Path(__file__).parent / "training_data.jsonl"

# ── System Prompt (matches backend/ai/prompt_templates.py GENERAL_SYSTEM) ────

SYSTEM_PROMPT = (
    "You are Concert Med Ops AI, a clinical decision support assistant for "
    "supervising physicians, paramedics, and harm reduction volunteers at live "
    "music events and EDM festivals. You provide rapid, actionable guidance on "
    "toxicology, overdose management, triage, and festival-specific emergencies. "
    "Always prioritise patient safety. For life-threatening emergencies, "
    "direct the user to activate EMS (call 911) immediately.\n\n"
    "⚠️ DISCLAIMER: AI-generated guidance. Not a substitute for licensed medical "
    "care. Final treatment and transport decisions rest with the supervising physician."
)

# ── QA Templates per protocol category ───────────────────────────────────────
# Each entry: (question_template, uses_text=True)
# {title} → chunk metadata title, {text} → full chunk text (stripped)

QA_TEMPLATES: dict[str, list[tuple[str, str]]] = {
    "heat_stroke": [
        (
            "A 23-year-old female is found in the medical tent with a temperature of 105°F, "
            "confusion, and diaphoresis after dancing for 4 hours. What are the immediate "
            "cooling interventions?",
            "Based on the {title}, {text}",
        ),
        (
            "What temperature threshold distinguishes mild heat illness from life-threatening "
            "heat stroke, and when should active cooling stop?",
            "{text}",
        ),
        (
            "An MDMA user has a rectal temperature of 104.5°F with altered consciousness. "
            "Walk me through the field treatment sequence.",
            "Per the {title}: {text}",
        ),
    ],
    "toxicology": [
        (
            "How do I clinically distinguish serotonin syndrome from heat stroke in a festival "
            "patient who took MDMA and is on an SSRI?",
            "{text}",
        ),
        (
            "A patient reports taking MDMA and is on sertraline daily. What are the Hunter "
            "Toxicity Criteria findings I should look for?",
            "According to the {title}: {text}",
        ),
        (
            "A patient presents confused and vomiting but friends report she drank 'gallons of "
            "water to stay safe' at the show. Should I give IV fluids? What is my differential?",
            "{text}",
        ),
        (
            "What are the key clinical differences between dehydration and hyponatremia in an "
            "MDMA user, and how does treatment differ?",
            "Per {title}: {text}",
        ),
        (
            "A patient went unconscious rapidly and friends say he 'had a cap of G with beers.' "
            "What is my management priority and why is there no antidote?",
            "{text}",
        ),
        (
            "A male patient with GHB intoxication is comatose but breathing. He is vomiting. "
            "What is the single most important positioning intervention and why?",
            "The {title} states: {text}",
        ),
    ],
    "overdose": [
        (
            "Medic Rover-2 finds an unresponsive patient near stage left with pinpoint pupils "
            "and snoring respirations. What are the first three steps?",
            "{text}",
        ),
        (
            "How do I dose intranasal Narcan in an unresponsive festival patient, and why "
            "should I keep them for observation even after they wake up?",
            "According to the {title}: {text}",
        ),
        (
            "What is the danger of giving too much naloxone too quickly to a physically "
            "dependent opioid user, and how do I titrate the dose?",
            "{text}",
        ),
        (
            "A patient reversed with naloxone 4mg intranasal starts to sedate again 45 minutes "
            "later. What should I do and why?",
            "Per {title}: {text}",
        ),
    ],
    "clinical": [
        (
            "A 19-year-old male has been dancing for 6 hours in 90°F heat and now has severe "
            "bilateral leg cramps and dark brown urine. What condition do I suspect and what "
            "is my immediate intervention?",
            "{text}",
        ),
        (
            "How do I calculate target IV fluid rate for rhabdomyolysis and what electrolyte "
            "should I watch most closely?",
            "Based on the {title}: {text}",
        ),
        (
            "Patient has possible rhabdomyolysis but urine output is not increasing despite "
            "500mL/hr NS. What should I stop doing and why?",
            "{text}",
        ),
    ],
    "harm_reduction": [
        (
            "A DanceSafe volunteer asks what color change on a Marquis reagent indicates MDMA. "
            "What should they look for and what limitations does reagent testing have?",
            "{text}",
        ),
        (
            "A festival attendee wants to know if their pill is safe after a Marquis test "
            "showed purple-black. How should I counsel them on residual fentanyl risk?",
            "{text}",
        ),
        (
            "What are the common reagent tests used at festivals and what substances does "
            "each one indicate?",
            "{text}",
        ),
    ],
    "triage": [
        (
            "In a mass casualty incident at the main stage, walk me through START triage "
            "categories and how to quickly sort patients in the field.",
            "{text}",
        ),
        (
            "When should I transport a festival patient to the hospital versus keeping them "
            "in the medical tent for observation? What are the red flag criteria?",
            "{text}",
        ),
        (
            "A patient refuses transport after a serious overdose reversal and appears "
            "lucid. What documentation do I need for Against Medical Advice (AMA)?",
            "{text}",
        ),
    ],
}

# ── Generic fallback templates used when category has no specific template ───

GENERIC_TEMPLATES: list[tuple[str, str]] = [
    (
        "Summarise the key clinical points from '{title}' for a festival paramedic.",
        "{text}",
    ),
    (
        "A medical volunteer asks: what does the '{title}' protocol say about immediate interventions?",
        "{text}",
    ),
    (
        "Quiz question: what are the three most important actions in the '{title}' protocol?",
        "{text}",
    ),
]

# ── Additional hand-crafted QA pairs (expert knowledge, not from KB) ─────────
# These supplement KB-derived pairs with reasoning-heavy examples the fine-tune needs.

HANDCRAFTED_PAIRS: list[dict[str, str]] = [
    {
        "question": "What three drug combinations at an EDM festival are most likely to cause serotonin syndrome?",
        "answer": (
            "The highest-risk polydrug combinations for serotonin syndrome at EDM festivals are:\n\n"
            "1. **MDMA + SSRIs/SNRIs** (e.g., sertraline, fluoxetine, venlafaxine) — MDMA floods "
            "the synapse with serotonin; SSRIs block its reuptake, causing dangerous excess.\n"
            "2. **MDMA + MAOIs** (including linezolid, methylene blue, or recreational "
            "harmaline/ayahuasca) — MAOIs prevent serotonin degradation, leading to severe, "
            "rapidly fatal serotonin syndrome.\n"
            "3. **MDMA + tramadol** — Tramadol has both serotonergic and weak opioid activity; "
            "combining with MDMA significantly elevates serotonin syndrome risk.\n\n"
            "Key differentiator from heat stroke: clonus (rhythmic muscle twitching), hyperreflexia, "
            "and bilateral Babinski signs point strongly toward serotonin syndrome.\n\n"
            "⚠️ DISCLAIMER: AI-generated guidance. Final treatment decisions rest with the supervising physician."
        ),
    },
    {
        "question": "A 24-year-old is found unresponsive. Friends say she 'took ketamine and drank all day.' GCS is 8, RR is 6, SpO2 is 88%. What do I do first?",
        "answer": (
            "Immediate priorities (first 60 seconds):\n\n"
            "1. **Airway** — Position: jaw thrust + head-tilt if no trauma suspected. "
            "Suction if vomit present. Insert nasopharyngeal airway if tolerated.\n"
            "2. **Breathing** — SpO2 88% and RR 6 = respiratory failure. Start BVM ventilations "
            "at 10-12 breaths/min with 100% O2. Do NOT wait.\n"
            "3. **Consider naloxone** — Ketamine alone does not cause respiratory depression at "
            "recreational doses, but fentanyl contamination in 'ketamine' is common. Give 4mg "
            "intranasal naloxone empirically; it is safe even if opioids are not confirmed.\n"
            "4. **IV access + glucose check** — Rule out hypoglycaemia as a co-factor.\n"
            "5. **Activate EMS transport** — GCS 8 + respiratory failure = mandatory transport. "
            "This patient cannot be managed in a festival tent.\n\n"
            "Key point: ketamine + alcohol is a CNS depressant combination that potentiates "
            "respiratory depression beyond what either drug causes alone.\n\n"
            "⚠️ DISCLAIMER: AI-generated guidance. Final treatment decisions rest with the supervising physician."
        ),
    },
    {
        "question": "How do I differentiate excited delirium from serotonin syndrome in an agitated, hyperthermic patient?",
        "answer": (
            "Both present with agitation, hyperthermia, and tachycardia — the key differentiator "
            "is **neuromuscular findings**:\n\n"
            "| Feature | Serotonin Syndrome | Excited Delirium / Sympathomimetic Toxicity |\n"
            "|---|---|---|\n"
            "| Clonus | ✅ Yes (hallmark) | ❌ Absent |\n"
            "| Hyperreflexia | ✅ Yes | ❌ Normal/absent |\n"
            "| Rigidity pattern | Extremity > trunk | Diffuse lead-pipe rigidity |\n"
            "| Onset | Rapid (minutes after drug) | Rapid (stimulant peak) |\n"
            "| Serotonergic drug Hx | ✅ Required (MDMA + SSRI/MAOI) | Not required |\n\n"
            "**Treatment is the same first-line regardless**: benzodiazepines (midazolam 5mg IM or "
            "diazepam 10mg IV) and aggressive active cooling. Avoid haloperidol in serotonin "
            "syndrome (lowers seizure threshold and impairs heat dissipation).\n\n"
            "⚠️ DISCLAIMER: AI-generated guidance. Final treatment decisions rest with the supervising physician."
        ),
    },
    {
        "question": "What is the Gorge Amphitheatre medical transport plan and when should I call for Level 1 Trauma vs. Level 3?",
        "answer": (
            "Transport hierarchy from The Gorge Amphitheatre, George WA:\n\n"
            "1. **Quincy Valley Medical Center** (~25 min) — Minor only: simple lac repair, "
            "imaging for isolated extremity fracture. No trauma designation, no ICU.\n"
            "2. **Samaritan Hospital, Moses Lake** (~43 min, Level 3) — Moderate-to-severe: "
            "rhabdomyolysis needing renal monitoring, controlled seizures, moderate overdose "
            "requiring IV therapy beyond tent capability.\n"
            "3. **Central Washington Hospital, Wenatchee** (~59 min, Level 3) — Full capability: "
            "ICU, cardiac, psych holds.\n"
            "4. **Harborview Medical Center, Seattle** (~3 hr, Level 1) — Life-threatening only: "
            "penetrating trauma, neurosurgical emergency, severe burns, ECMO candidate.\n\n"
            "**Helicopter (HEMS)**: Request via 911 for any Level 1-bound patient or when "
            "ground transport time would be clinically unacceptable (e.g., ROSC after cardiac arrest).\n\n"
            "⚠️ Remember: every ground transport removes 1 ambulance and 2 crew for 1–3 hours. "
            "The treat-on-site threshold should be high.\n\n"
            "⚠️ DISCLAIMER: AI-generated guidance. Final treatment decisions rest with the supervising physician."
        ),
    },
    {
        "question": "A Marquis test on a white powder shows a rapid orange-to-brown colour change instead of purple-black. What does this suggest and what should the patient do?",
        "answer": (
            "A Marquis reagent reaction of **orange-to-brown** is NOT consistent with MDMA "
            "(which produces purple → black). Possible interpretations:\n\n"
            "- **Methamphetamine / amphetamine**: Marquis → orange to brown-black\n"
            "- **DXM (dextromethorphan)**: Marquis → orange-red\n"
            "- **Caffeine / other adulterants**: variable pale orange\n"
            "- **Fentanyl**: Marquis → no reaction (use a fentanyl test strip separately)\n\n"
            "**Critical caveat**: Reagent tests indicate the *presence* of a substance class, "
            "not purity or exact dose. A purple-black reaction does not rule out fentanyl "
            "contamination — always recommend a fentanyl test strip as an additional check.\n\n"
            "**Counselling guidance**: Explain the result non-judgementally. The substance is "
            "not what the person expected. Advise: do not consume, or if already consumed, "
            "stay with friends, avoid mixing with alcohol/opioids, and come to medical tent "
            "immediately if feeling unwell.\n\n"
            "⚠️ DISCLAIMER: Reagent testing is a harm reduction tool, not a definitive "
            "analytical method. AI-generated guidance only."
        ),
    },
    {
        "question": "Can I give oral fluids to a hyponatraemic festival patient who is vomiting and confused?",
        "answer": (
            "**No** — oral fluids are contraindicated in a hyponatraemic patient who is "
            "vomiting and confused.\n\n"
            "Reasoning:\n"
            "- Vomiting prevents reliable absorption and raises aspiration risk.\n"
            "- Confusion (altered GCS) suggests the sodium is already critically low — "
            "further free water will worsen cerebral oedema.\n"
            "- Hyponatraemia from MDMA-related SIADH requires **fluid restriction**, "
            "not more fluid.\n\n"
            "Correct management:\n"
            "1. Stop all hypotonic fluids (free water, sports drinks, regular saline in "
            "excess).\n"
            "2. If the patient has active seizures or rapidly declining GCS → administer "
            "Hypertonic Saline (3% NaCl) 100 mL IV over 10 minutes, repeat up to 3× "
            "per physician order.\n"
            "3. Secure IV access; position for airway protection.\n"
            "4. Transport to emergency department — severe hyponatraemia cannot be safely "
            "corrected in a festival tent.\n\n"
            "⚠️ DISCLAIMER: AI-generated guidance. Final treatment decisions rest with the supervising physician."
        ),
    },
]


# ── Helper functions ──────────────────────────────────────────────────────────

def _strip_text(text: str) -> str:
    """Collapse multi-line whitespace for cleaner training text."""
    return re.sub(r"\n{3,}", "\n\n", text.strip())


def _fill_answer(template: str, chunk: dict[str, Any]) -> str:
    title = chunk.get("metadata", {}).get("title", "Protocol")
    text = _strip_text(chunk["text"])
    answer = template.format(title=title, text=text)
    if "DISCLAIMER" not in answer:
        answer += (
            "\n\n⚠️ DISCLAIMER: AI-generated guidance. "
            "Final treatment decisions rest with the supervising physician."
        )
    return answer


def kb_to_qa_pairs(kb: list[dict]) -> list[dict[str, str]]:
    """
    Expand each KB chunk into (question, answer) dicts.

    Selects templates based on chunk category, falling back to generic
    templates for categories with no specific match.
    """
    pairs: list[dict[str, str]] = []
    for collection in kb:
        for chunk in collection.get("chunks", []):
            category = chunk.get("metadata", {}).get("category", "")
            templates = QA_TEMPLATES.get(category, GENERIC_TEMPLATES)
            for q_template, a_template in templates:
                title = chunk.get("metadata", {}).get("title", "Protocol")
                question = q_template.format(title=title)
                answer = _fill_answer(a_template, chunk)
                pairs.append({"question": question, "answer": answer})
    return pairs


def to_sharegpt(qa: dict[str, str], system: str = SYSTEM_PROMPT) -> dict:
    """
    Wrap a QA pair in ShareGPT conversation format.

    Unsloth SFTTrainer expects this schema when dataset_text_field is not used:
      {"conversations": [
          {"from": "system", "value": "..."},
          {"from": "human", "value": "..."},
          {"from": "gpt",   "value": "..."}
      ]}

    Ref: https://docs.unsloth.ai/basics/datasets-guide#conversational
    """
    return {
        "conversations": [
            {"from": "system", "value": system},
            {"from": "human", "value": qa["question"]},
            {"from": "gpt", "value": qa["answer"]},
        ]
    }


def to_alpaca(qa: dict[str, str], system: str = SYSTEM_PROMPT) -> dict:
    """
    Wrap a QA pair in Alpaca prompt format.

    Schema: {"instruction": "...", "input": "", "output": "..."}
    Ref: https://docs.unsloth.ai/basics/datasets-guide#instruction
    """
    return {
        "instruction": system,
        "input": qa["question"],
        "output": qa["answer"],
    }


TAG_TO_CATEGORY_MAP = {
    "serotonin_syndrome": "toxicology",
    "hyponatremia": "toxicology",
    "ghb_intoxication": "toxicology",
    "withdrawal": "toxicology",
    "opioid_overdose": "overdose",
    "agitation": "clinical",
    "rhabdomyolysis": "clinical",
    "triage_mci": "triage",
    "transport": "triage",
    "mass_gathering_ops": "triage",
    "harm_reduction": "harm_reduction",
    "heat_stroke": "heat_stroke"
}


def load_kb_from_sqlite(db_path: pathlib.Path) -> list[dict]:
    import sqlite3
    if not db_path.exists():
        raise FileNotFoundError(f"SQLite knowledge database not found: {db_path}")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute("SELECT collection, text, metadata, chunk_id FROM rag_chunks").fetchall()
    except sqlite3.OperationalError as exc:
        conn.close()
        raise RuntimeError(f"Failed to query rag_chunks. Make sure database is initialized and ingested: {exc}")

    collections: dict[str, list[dict]] = {}
    for r in rows:
        col = r["collection"]
        try:
            meta = json.loads(r["metadata"]) if r["metadata"] else {}
        except Exception:
            meta = {}

        # Determine category for QA templates
        if "category" not in meta:
            # Try to map condition tags
            tags = meta.get("condition_tags", [])
            mapped_category = None
            for tag in tags:
                if tag in TAG_TO_CATEGORY_MAP:
                    mapped_category = TAG_TO_CATEGORY_MAP[tag]
                    break
            meta["category"] = mapped_category or "clinical"

        # Ensure page/section info is clean for _fill_answer
        if "page" not in meta:
            if "page_start" in meta:
                meta["page"] = meta["page_start"]
            elif "section" in meta:
                meta["page"] = meta["section"]

        chunk = {
            "id": r["chunk_id"],
            "text": r["text"],
            "metadata": meta
        }
        collections.setdefault(col, []).append(chunk)

    conn.close()

    return [
        {"collection": name, "chunks": chunks}
        for name, chunks in collections.items()
    ]


def build_dataset(
    kb_path: pathlib.Path | None = KB_PATH,
    sqlite_path: pathlib.Path | None = None,
    fmt: str = "sharegpt",
    shuffle_seed: int | None = 42,
) -> list[dict]:
    """
    Load KB, expand to QA pairs, add handcrafted pairs, format, and optionally shuffle.

    Args:
        kb_path: Path to harm_reduction_kb.json.
        sqlite_path: Path to knowledge.sqlite database.
        fmt: Output format — "sharegpt" (default) or "alpaca".
        shuffle_seed: Random seed for reproducible shuffling. None = no shuffle.

    Returns:
        List of formatted training examples.
    """
    if sqlite_path is not None:
        kb = load_kb_from_sqlite(sqlite_path)
    else:
        if kb_path is None or not kb_path.exists():
            raise FileNotFoundError(f"Knowledge base not found: {kb_path}")
        with kb_path.open(encoding="utf-8") as f:
            kb = json.load(f)

    pairs = kb_to_qa_pairs(kb) + HANDCRAFTED_PAIRS

    formatter = to_sharegpt if fmt == "sharegpt" else to_alpaca
    examples = [formatter(p) for p in pairs]

    if shuffle_seed is not None:
        rng = random.Random(shuffle_seed)
        rng.shuffle(examples)

    return examples


def write_jsonl(examples: list[dict], output_path: pathlib.Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        for ex in examples:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    # Ensure stdout handles UTF-8 on Windows
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    parser = argparse.ArgumentParser(
        description="Generate Unsloth fine-tune training data from the Concert Med Ops KB."
    )
    parser.add_argument(
        "--kb", type=pathlib.Path, default=KB_PATH,
        help="Path to harm_reduction_kb.json",
    )
    parser.add_argument(
        "--sqlite", type=pathlib.Path, default=None,
        help="Path to knowledge.sqlite (extracts training examples from all ingested PDFs/HTML)",
    )
    parser.add_argument(
        "--output", "-o", type=pathlib.Path, default=DEFAULT_OUTPUT,
        help="Output JSONL path (default: notebooks/training_data.jsonl)",
    )
    parser.add_argument(
        "--format", choices=["sharegpt", "alpaca"], default="sharegpt",
        help="Training data format (default: sharegpt)",
    )
    parser.add_argument(
        "--no-shuffle", action="store_true",
        help="Disable shuffling (output will follow KB order)",
    )
    args = parser.parse_args()

    seed = None if args.no_shuffle else 42
    if args.sqlite:
        examples = build_dataset(kb_path=None, sqlite_path=args.sqlite, fmt=args.format, shuffle_seed=seed)
    else:
        examples = build_dataset(kb_path=args.kb, sqlite_path=None, fmt=args.format, shuffle_seed=seed)
        
    write_jsonl(examples, args.output)

    print(f"✅ Generated {len(examples)} training examples → {args.output}")
    print(f"   Format: {args.format}")
    if args.sqlite:
        print(f"   Source: SQLite ({args.sqlite})")
    else:
        print(f"   Source: KB ({args.kb})")

    # Print a sample
    print("\n── Sample (first example) ──────────────────────────────────────────")
    sample = examples[0]
    if args.format == "sharegpt":
        convs = sample["conversations"]
        print(f"[system]: {convs[0]['value'][:120]}...")
        print(f"[human]:  {convs[1]['value']}")
        print(f"[gpt]:    {convs[2]['value'][:200]}...")
    else:
        print(f"instruction: {sample['instruction'][:80]}...")
        print(f"input:  {sample['input']}")
        print(f"output: {sample['output'][:200]}...")


if __name__ == "__main__":
    main()
