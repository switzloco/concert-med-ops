"""
Tests for notebooks/generate_training_data.py

Verifies KB loading, QA pair expansion, ShareGPT/Alpaca format compliance,
JSONL round-trips, and edge cases the fine-tune pipeline depends on.

Run from repo root:
    pytest notebooks/test_generate_training_data.py -v
"""

import json
import pathlib
import sys
import tempfile
import textwrap

import pytest

# Allow importing from notebooks/ without installing the package
sys.path.insert(0, str(pathlib.Path(__file__).parent))

from generate_training_data import (
    HANDCRAFTED_PAIRS,
    KB_PATH,
    SYSTEM_PROMPT,
    QA_TEMPLATES,
    build_dataset,
    kb_to_qa_pairs,
    to_alpaca,
    to_sharegpt,
    write_jsonl,
    _strip_text,
    _fill_answer,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

MINIMAL_KB = [
    {
        "collection": "harm_reduction_protocols",
        "chunks": [
            {
                "id": "proto-test-overdose",
                "text": (
                    "PROTOCOL: OPIOID OVERDOSE\n"
                    "1. Check airway.\n"
                    "2. Administer naloxone 4mg intranasal.\n"
                    "3. Monitor for re-sedation."
                ),
                "metadata": {
                    "title": "Opioid Overdose Protocol",
                    "category": "overdose",
                    "page": 1,
                },
            },
            {
                "id": "proto-test-heat",
                "text": "Apply evaporative cooling. Target temp < 101.5°F before stopping.",
                "metadata": {
                    "title": "Active Cooling Protocol",
                    "category": "heat_stroke",
                    "page": 2,
                },
            },
        ],
    }
]

UNKNOWN_CATEGORY_KB = [
    {
        "collection": "harm_reduction_protocols",
        "chunks": [
            {
                "id": "proto-unknown",
                "text": "Some protocol text that doesn't match any template category.",
                "metadata": {
                    "title": "Mystery Protocol",
                    "category": "unknown_category_xyz",
                    "page": 99,
                },
            }
        ],
    }
]


@pytest.fixture()
def minimal_kb_file(tmp_path: pathlib.Path) -> pathlib.Path:
    p = tmp_path / "test_kb.json"
    p.write_text(json.dumps(MINIMAL_KB))
    return p


@pytest.fixture()
def unknown_category_kb_file(tmp_path: pathlib.Path) -> pathlib.Path:
    p = tmp_path / "unknown_kb.json"
    p.write_text(json.dumps(UNKNOWN_CATEGORY_KB))
    return p


# ── _strip_text ───────────────────────────────────────────────────────────────

class TestStripText:
    def test_collapses_triple_newlines(self):
        result = _strip_text("Line 1\n\n\n\nLine 2")
        assert "\n\n\n" not in result
        assert "Line 1" in result
        assert "Line 2" in result

    def test_strips_leading_trailing_whitespace(self):
        result = _strip_text("   text   ")
        assert result == "text"

    def test_preserves_double_newlines(self):
        result = _strip_text("Para 1\n\nPara 2")
        assert "Para 1\n\nPara 2" == result

    def test_handles_empty_string(self):
        assert _strip_text("") == ""


# ── _fill_answer ──────────────────────────────────────────────────────────────

class TestFillAnswer:
    def test_title_substitution(self):
        chunk = {"text": "Some text.", "metadata": {"title": "Test Protocol"}}
        result = _fill_answer("From {title}: {text}", chunk)
        assert "Test Protocol" in result
        assert "Some text." in result

    def test_disclaimer_appended_when_missing(self):
        chunk = {"text": "Plain answer.", "metadata": {"title": "X"}}
        result = _fill_answer("{text}", chunk)
        assert "DISCLAIMER" in result

    def test_disclaimer_not_duplicated_when_present(self):
        chunk = {
            "text": "Answer with ⚠️ DISCLAIMER already here.",
            "metadata": {"title": "X"},
        }
        result = _fill_answer("{text}", chunk)
        assert result.count("DISCLAIMER") == 1

    def test_missing_title_falls_back_to_protocol(self):
        chunk = {"text": "No metadata.", "metadata": {}}
        result = _fill_answer("See {title}.", chunk)
        assert "Protocol" in result


# ── kb_to_qa_pairs ────────────────────────────────────────────────────────────

class TestKbToQaPairs:
    def test_returns_list_of_dicts(self):
        pairs = kb_to_qa_pairs(MINIMAL_KB)
        assert isinstance(pairs, list)
        assert len(pairs) > 0
        for p in pairs:
            assert "question" in p
            assert "answer" in p

    def test_each_pair_is_non_empty(self):
        pairs = kb_to_qa_pairs(MINIMAL_KB)
        for p in pairs:
            assert p["question"].strip()
            assert p["answer"].strip()

    def test_overdose_category_produces_multiple_pairs(self):
        pairs = kb_to_qa_pairs(MINIMAL_KB)
        overdose_templates = QA_TEMPLATES.get("overdose", [])
        overdose_pairs = [
            p for p in pairs
            if "naloxone" in p["question"].lower() or "opioid" in p["question"].lower()
               or "unresponsive" in p["question"].lower() or "Narcan" in p["question"]
        ]
        assert len(overdose_pairs) >= 1

    def test_unknown_category_uses_generic_templates(self):
        pairs = kb_to_qa_pairs(UNKNOWN_CATEGORY_KB)
        assert len(pairs) > 0
        for p in pairs:
            assert "Mystery Protocol" in p["question"] or "Mystery Protocol" in p["answer"]

    def test_all_answers_contain_disclaimer(self):
        pairs = kb_to_qa_pairs(MINIMAL_KB)
        for p in pairs:
            assert "DISCLAIMER" in p["answer"], f"No disclaimer in: {p['answer'][:80]}"

    def test_question_references_chunk_content(self):
        pairs = kb_to_qa_pairs(MINIMAL_KB)
        # At least some questions should reference the KB titles or clinical content
        titles = {"Opioid Overdose Protocol", "Active Cooling Protocol"}
        answered = set()
        for p in pairs:
            for t in titles:
                if t in p["question"] or t in p["answer"]:
                    answered.add(t)
        assert len(answered) >= 1


# ── to_sharegpt ───────────────────────────────────────────────────────────────

class TestToShareGPT:
    """
    Validates ShareGPT conversation format.
    Ref: https://docs.unsloth.ai/basics/datasets-guide#conversational
    """

    def test_top_level_key(self):
        result = to_sharegpt({"question": "Q?", "answer": "A."})
        assert "conversations" in result

    def test_three_turns(self):
        result = to_sharegpt({"question": "Q?", "answer": "A."})
        convs = result["conversations"]
        assert len(convs) == 3

    def test_turn_order(self):
        result = to_sharegpt({"question": "Q?", "answer": "A."})
        froms = [c["from"] for c in result["conversations"]]
        assert froms == ["system", "human", "gpt"]

    def test_system_value_matches_default(self):
        result = to_sharegpt({"question": "Q?", "answer": "A."})
        assert result["conversations"][0]["value"] == SYSTEM_PROMPT

    def test_custom_system_prompt(self):
        result = to_sharegpt({"question": "Q?", "answer": "A."}, system="Custom sys")
        assert result["conversations"][0]["value"] == "Custom sys"

    def test_question_in_human_turn(self):
        result = to_sharegpt({"question": "What is naloxone?", "answer": "An opioid antagonist."})
        assert result["conversations"][1]["value"] == "What is naloxone?"

    def test_answer_in_gpt_turn(self):
        result = to_sharegpt({"question": "Q?", "answer": "An opioid antagonist."})
        assert result["conversations"][2]["value"] == "An opioid antagonist."

    def test_each_turn_has_from_and_value(self):
        result = to_sharegpt({"question": "Q?", "answer": "A."})
        for turn in result["conversations"]:
            assert "from" in turn
            assert "value" in turn
            assert isinstance(turn["value"], str)

    def test_json_serialisable(self):
        result = to_sharegpt({"question": "Q?", "answer": "A."})
        serialised = json.dumps(result)
        assert json.loads(serialised) == result


# ── to_alpaca ─────────────────────────────────────────────────────────────────

class TestToAlpaca:
    """
    Validates Alpaca instruction format.
    Ref: https://docs.unsloth.ai/basics/datasets-guide#instruction
    """

    def test_required_keys(self):
        result = to_alpaca({"question": "Q?", "answer": "A."})
        assert "instruction" in result
        assert "input" in result
        assert "output" in result

    def test_instruction_is_system_prompt(self):
        result = to_alpaca({"question": "Q?", "answer": "A."})
        assert result["instruction"] == SYSTEM_PROMPT

    def test_input_is_question(self):
        result = to_alpaca({"question": "What is MDMA?", "answer": "A stimulant."})
        assert result["input"] == "What is MDMA?"

    def test_output_is_answer(self):
        result = to_alpaca({"question": "Q?", "answer": "A stimulant."})
        assert result["output"] == "A stimulant."

    def test_json_serialisable(self):
        result = to_alpaca({"question": "Q?", "answer": "A."})
        assert json.loads(json.dumps(result)) == result


# ── build_dataset ─────────────────────────────────────────────────────────────

class TestBuildDataset:
    def test_raises_on_missing_kb(self, tmp_path):
        with pytest.raises(FileNotFoundError, match="Knowledge base not found"):
            build_dataset(kb_path=tmp_path / "does_not_exist.json")

    def test_returns_list(self, minimal_kb_file):
        result = build_dataset(kb_path=minimal_kb_file)
        assert isinstance(result, list)

    def test_sharegpt_format_default(self, minimal_kb_file):
        result = build_dataset(kb_path=minimal_kb_file)
        assert all("conversations" in ex for ex in result)

    def test_alpaca_format(self, minimal_kb_file):
        result = build_dataset(kb_path=minimal_kb_file, fmt="alpaca")
        assert all("instruction" in ex and "input" in ex and "output" in ex for ex in result)

    def test_includes_handcrafted_pairs(self, minimal_kb_file):
        result = build_dataset(kb_path=minimal_kb_file)
        # Count: KB pairs + len(HANDCRAFTED_PAIRS)
        assert len(result) >= len(HANDCRAFTED_PAIRS)

    def test_shuffle_is_reproducible(self, minimal_kb_file):
        r1 = build_dataset(kb_path=minimal_kb_file, shuffle_seed=99)
        r2 = build_dataset(kb_path=minimal_kb_file, shuffle_seed=99)
        assert r1 == r2

    def test_different_seeds_give_different_order(self, minimal_kb_file):
        r1 = build_dataset(kb_path=minimal_kb_file, shuffle_seed=1)
        r2 = build_dataset(kb_path=minimal_kb_file, shuffle_seed=2)
        # There's an astronomically small chance this fails — acceptable
        assert r1 != r2

    def test_no_shuffle(self, minimal_kb_file):
        r1 = build_dataset(kb_path=minimal_kb_file, shuffle_seed=None)
        r2 = build_dataset(kb_path=minimal_kb_file, shuffle_seed=None)
        assert r1 == r2

    def test_total_count_with_real_kb(self):
        if not KB_PATH.exists():
            pytest.skip("Real harm_reduction_kb.json not available in this environment")
        result = build_dataset(kb_path=KB_PATH)
        # Should have at least 1 example per KB chunk + handcrafted pairs
        assert len(result) >= len(HANDCRAFTED_PAIRS)
        assert len(result) > 0


# ── write_jsonl ───────────────────────────────────────────────────────────────

class TestWriteJsonl:
    def test_creates_file(self, tmp_path):
        out = tmp_path / "out.jsonl"
        write_jsonl([{"key": "value"}], out)
        assert out.exists()

    def test_creates_parent_directories(self, tmp_path):
        out = tmp_path / "nested" / "deep" / "out.jsonl"
        write_jsonl([{"key": "value"}], out)
        assert out.exists()

    def test_one_line_per_example(self, tmp_path):
        examples = [{"a": 1}, {"b": 2}, {"c": 3}]
        out = tmp_path / "out.jsonl"
        write_jsonl(examples, out)
        lines = out.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 3

    def test_each_line_is_valid_json(self, tmp_path):
        examples = [
            to_sharegpt({"question": f"Q{i}?", "answer": f"A{i}."}) for i in range(5)
        ]
        out = tmp_path / "out.jsonl"
        write_jsonl(examples, out)
        for line in out.read_text(encoding="utf-8").strip().splitlines():
            parsed = json.loads(line)
            assert "conversations" in parsed

    def test_round_trip_sharegpt(self, tmp_path):
        original = [to_sharegpt({"question": "Q?", "answer": "A."})]
        out = tmp_path / "out.jsonl"
        write_jsonl(original, out)
        loaded = [json.loads(l) for l in out.read_text(encoding="utf-8").strip().splitlines()]
        assert loaded == original

    def test_unicode_preserved(self, tmp_path):
        out = tmp_path / "unicode.jsonl"
        write_jsonl([{"text": "Naloxone 4mg — nasal spray ✅"}], out)
        loaded = json.loads(out.read_text(encoding="utf-8").strip())
        assert "✅" in loaded["text"]

    def test_overwrites_existing_file(self, tmp_path):
        out = tmp_path / "out.jsonl"
        write_jsonl([{"first": True}], out)
        write_jsonl([{"second": True}, {"third": True}], out)
        lines = out.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 2
        assert json.loads(lines[0]) == {"second": True}


# ── HANDCRAFTED_PAIRS ─────────────────────────────────────────────────────────

class TestHandcraftedPairs:
    def test_all_pairs_have_question_and_answer(self):
        for p in HANDCRAFTED_PAIRS:
            assert "question" in p, f"Missing 'question' in pair: {p}"
            assert "answer" in p, f"Missing 'answer' in pair: {p}"

    def test_all_answers_have_disclaimer(self):
        for p in HANDCRAFTED_PAIRS:
            assert "DISCLAIMER" in p["answer"], (
                f"Missing disclaimer in: {p['question'][:60]}"
            )

    def test_all_questions_are_non_empty(self):
        for p in HANDCRAFTED_PAIRS:
            assert p["question"].strip()

    def test_all_answers_are_substantive(self):
        for p in HANDCRAFTED_PAIRS:
            # Require at least 100 chars of content — not a stub
            assert len(p["answer"]) >= 100, (
                f"Answer too short ({len(p['answer'])} chars): {p['question'][:60]}"
            )

    def test_clinical_accuracy_keywords(self):
        """Smoke-test that high-risk clinical answers contain expected terms."""
        all_answers = " ".join(p["answer"] for p in HANDCRAFTED_PAIRS)
        # Key clinical terms that must appear somewhere in the handcrafted set
        required = [
            "naloxone", "serotonin", "clonus", "benzodiazepine",
            "hypertonic", "transport",
        ]
        for term in required:
            assert term.lower() in all_answers.lower(), (
                f"Expected clinical term '{term}' not found in any handcrafted answer"
            )


# ── Integration: full pipeline ────────────────────────────────────────────────

class TestFullPipeline:
    def test_full_sharegpt_pipeline(self, minimal_kb_file, tmp_path):
        output = tmp_path / "train.jsonl"
        examples = build_dataset(kb_path=minimal_kb_file, fmt="sharegpt")
        write_jsonl(examples, output)

        lines = output.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == len(examples)

        for line in lines:
            ex = json.loads(line)
            convs = ex["conversations"]
            assert convs[0]["from"] == "system"
            assert convs[1]["from"] == "human"
            assert convs[2]["from"] == "gpt"
            assert convs[2]["value"].strip()  # answer is non-empty

    def test_full_alpaca_pipeline(self, minimal_kb_file, tmp_path):
        output = tmp_path / "train_alpaca.jsonl"
        examples = build_dataset(kb_path=minimal_kb_file, fmt="alpaca")
        write_jsonl(examples, output)

        for line in output.read_text(encoding="utf-8").strip().splitlines():
            ex = json.loads(line)
            assert ex["instruction"]
            assert ex["input"]
            assert ex["output"]

    def test_dataset_suitable_for_unsloth_sft(self, minimal_kb_file):
        """
        Validate that the dataset structure matches what Unsloth SFTTrainer
        expects for conversational data.

        Ref: https://docs.unsloth.ai/basics/datasets-guide#conversational
        The key requirements are:
          - Top-level key: "conversations"
          - Each conversation is a list of dicts with "from" and "value" keys
          - "from" values must be: "system", "human", "gpt"
          - "gpt" turn must be non-empty (the training target)
        """
        examples = build_dataset(kb_path=minimal_kb_file, fmt="sharegpt")
        for ex in examples:
            assert "conversations" in ex
            convs = ex["conversations"]
            for turn in convs:
                assert "from" in turn
                assert "value" in turn
                assert turn["from"] in {"system", "human", "gpt"}
            # The gpt (model) turn must have content — this is the training label
            gpt_turns = [t for t in convs if t["from"] == "gpt"]
            assert len(gpt_turns) == 1
            assert gpt_turns[0]["value"].strip()
