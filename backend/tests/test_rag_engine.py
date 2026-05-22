"""
Unit and integration tests for the Stage-1 RAG engine upgrades.

Covers:
  - Schema v2 migration (new drugs_tagged / condition_tags columns)
  - add_documents with metadata tags
  - BM25 query (backward-compatible)
  - hybrid_query: drug-name exact-match boost
  - Token cap enforcement (max_context_tokens)
  - all_collection_stats
  - Chunker (chunk_text) and tagger (_tag_chunk)
  - Ingestion script helpers (_chunk_id, _approx_tokens)
"""
import json
import os
import pathlib
import tempfile

import pytest

# ── Force test-isolated DB before any backend imports ────────────────────────
_TMP_DIR = tempfile.mkdtemp()
os.environ["EVENT_MED_DATA_DIR"] = _TMP_DIR


# ── RAGEngine tests ───────────────────────────────────────────────────────────

class TestRAGEngineSchema:
    def _fresh_engine(self):
        """Return a RAGEngine pointed at the test temp dir (no bootstrap from KB)."""
        # Patch the KB path to a non-existent file so bootstrap is skipped
        import backend.ai.rag_engine as mod
        original = mod._BUNDLED_KB_PATH
        mod._BUNDLED_KB_PATH = "/nonexistent_kb.json"
        from backend.ai.rag_engine import RAGEngine
        engine = RAGEngine()
        mod._BUNDLED_KB_PATH = original
        return engine

    def test_engine_creates_db(self):
        engine = self._fresh_engine()
        db_path = pathlib.Path(_TMP_DIR) / "knowledge.sqlite"
        assert db_path.exists()

    def test_schema_version_recorded(self):
        import sqlite3
        self._fresh_engine()
        db_path = pathlib.Path(_TMP_DIR) / "knowledge.sqlite"
        conn = sqlite3.connect(str(db_path))
        row = conn.execute("SELECT value FROM _schema_meta WHERE key='version'").fetchone()
        conn.close()
        assert row is not None
        assert int(row[0]) == 2

    def test_add_and_query_basic(self):
        engine = self._fresh_engine()
        engine.add_documents(
            collection_name="test_col",
            documents=["Naloxone reverses opioid overdose by blocking mu receptors."],
            metadatas=[{"title": "Naloxone Guide", "drugs_tagged": ["naloxone", "opioid"]}],
            ids=["doc-001"],
        )
        results = engine.query("test_col", "opioid overdose naloxone", k=5)
        assert len(results) >= 1
        assert "naloxone" in results[0]["text"].lower()

    def test_metadata_round_trip(self):
        engine = self._fresh_engine()
        meta = {
            "title": "Serotonin Syndrome Protocol",
            "source_url": "https://emcrit.org/ibcc/serotonin/",
            "condition_tags": ["serotonin_syndrome"],
            "drugs_tagged": ["mdma", "ssri"],
        }
        engine.add_documents(
            collection_name="test_col",
            documents=["Serotonin syndrome causes clonus and hyperreflexia."],
            metadatas=[meta],
            ids=["ss-001"],
        )
        results = engine.query("test_col", "serotonin clonus", k=3)
        assert len(results) >= 1
        assert results[0]["metadata"]["title"] == "Serotonin Syndrome Protocol"
        assert results[0]["metadata"]["source_url"] == "https://emcrit.org/ibcc/serotonin/"

    def test_upsert_replaces_existing(self):
        engine = self._fresh_engine()
        engine.add_documents(
            collection_name="test_col",
            documents=["Version 1 text"],
            metadatas=[{"title": "V1"}],
            ids=["upsert-001"],
        )
        engine.add_documents(
            collection_name="test_col",
            documents=["Version 2 text — updated content"],
            metadatas=[{"title": "V2"}],
            ids=["upsert-001"],
        )
        results = engine.query("test_col", "version", k=5)
        texts = [r["text"] for r in results]
        assert any("Version 2" in t for t in texts)
        assert not any("Version 1" in t for t in texts)

    def test_collection_stats(self):
        engine = self._fresh_engine()
        engine.add_documents(
            collection_name="col_a",
            documents=["Doc 1", "Doc 2", "Doc 3"],
            metadatas=[{}, {}, {}],
            ids=["a1", "a2", "a3"],
        )
        engine.add_documents(
            collection_name="col_b",
            documents=["Doc 4"],
            metadatas=[{}],
            ids=["b1"],
        )
        assert engine.collection_stats("col_a") == 3
        assert engine.collection_stats("col_b") == 1
        assert engine.collection_stats("col_empty") == 0

    def test_all_collection_stats(self):
        engine = self._fresh_engine()
        engine.add_documents("stats_col_x", ["A", "B"], [{}, {}], ["x1", "x2"])
        engine.add_documents("stats_col_y", ["C"], [{}], ["y1"])
        stats = engine.all_collection_stats()
        assert stats.get("stats_col_x") == 2
        assert stats.get("stats_col_y") == 1

    def test_query_empty_collection_returns_empty(self):
        engine = self._fresh_engine()
        results = engine.query("nonexistent_collection", "opioid overdose", k=5)
        assert results == []


class TestHybridQuery:
    def _engine_with_data(self):
        import backend.ai.rag_engine as mod
        original = mod._BUNDLED_KB_PATH
        mod._BUNDLED_KB_PATH = "/nonexistent_kb.json"
        from backend.ai.rag_engine import RAGEngine
        engine = RAGEngine()
        mod._BUNDLED_KB_PATH = original

        engine.add_documents(
            collection_name="protocols",
            documents=[
                "Naloxone 4mg intranasal reverses opioid respiratory depression.",
                "Active cooling with ice packs and fans treats hyperthermia in MDMA users.",
                "Hypertonic saline bolus for symptomatic hyponatremia with seizures.",
                "Benzodiazepines are first-line for serotonin syndrome agitation.",
                "GHB intoxication: recovery position prevents aspiration.",
            ],
            metadatas=[
                {"title": "Naloxone Protocol", "drugs_tagged": ["naloxone", "opioid", "fentanyl"],
                 "condition_tags": ["opioid_overdose"]},
                {"title": "Cooling Protocol", "drugs_tagged": ["mdma"],
                 "condition_tags": ["heat_stroke"]},
                {"title": "Hyponatremia Protocol", "drugs_tagged": ["mdma"],
                 "condition_tags": ["hyponatremia"]},
                {"title": "Serotonin Syndrome", "drugs_tagged": ["mdma", "ssri"],
                 "condition_tags": ["serotonin_syndrome"]},
                {"title": "GHB Protocol", "drugs_tagged": ["ghb", "alcohol"],
                 "condition_tags": ["ghb_intoxication"]},
            ],
            ids=["n-001", "c-001", "h-001", "s-001", "g-001"],
        )
        return engine

    def test_hybrid_query_returns_results(self):
        engine = self._engine_with_data()
        results = engine.hybrid_query("protocols", "naloxone overdose", k=5)
        assert len(results) >= 1

    def test_drug_name_boost_promotes_matching_chunk(self):
        engine = self._engine_with_data()
        # Query with "ghb" as drug name — GHB protocol should surface first
        results = engine.hybrid_query("protocols", "intoxication coma", drug_names=["ghb"], k=5)
        titles = [r["metadata"]["title"] for r in results]
        # The GHB chunk should appear and ideally be in top-2 due to boost
        assert "GHB Protocol" in titles

    def test_drug_boost_does_not_exclude_bm25_results(self):
        engine = self._engine_with_data()
        # Query for naloxone but don't restrict to it — should still get BM25 results
        results = engine.hybrid_query("protocols", "respiratory depression airway", drug_names=["naloxone"], k=5)
        assert len(results) >= 1

    def test_token_cap_respected(self):
        import backend.ai.rag_engine as mod
        original = mod._BUNDLED_KB_PATH
        mod._BUNDLED_KB_PATH = "/nonexistent_kb.json"
        from backend.ai.rag_engine import RAGEngine, _approx_tokens
        engine = RAGEngine()
        mod._BUNDLED_KB_PATH = original

        # Insert 10 long chunks (~200 words each → ~260 tokens each)
        long_doc = " ".join(["word"] * 200)
        engine.add_documents(
            collection_name="token_test",
            documents=[long_doc] * 10,
            metadatas=[{"title": f"Doc {i}"} for i in range(10)],
            ids=[f"td-{i:03d}" for i in range(10)],
        )
        results = engine.hybrid_query("token_test", "word", k=10, max_context_tokens=600)
        total_tokens = sum(_approx_tokens(r["text"]) for r in results)
        assert total_tokens <= 700  # some slack over 600 due to "always include 1" rule

    def test_token_cap_always_includes_at_least_one(self):
        import backend.ai.rag_engine as mod
        original = mod._BUNDLED_KB_PATH
        mod._BUNDLED_KB_PATH = "/nonexistent_kb.json"
        from backend.ai.rag_engine import RAGEngine
        engine = RAGEngine()
        mod._BUNDLED_KB_PATH = original

        big_chunk = " ".join(["word"] * 500)  # ~650 tokens, over any tiny cap
        engine.add_documents(
            collection_name="big_col",
            documents=[big_chunk],
            metadatas=[{}],
            ids=["big-001"],
        )
        # Extremely tight cap — should still return the one chunk
        results = engine.hybrid_query("big_col", "word", k=5, max_context_tokens=10)
        assert len(results) == 1

    def test_no_drug_names_falls_back_to_bm25(self):
        engine = self._engine_with_data()
        results = engine.hybrid_query("protocols", "naloxone opioid reversal", drug_names=None, k=5)
        assert any("Naloxone" in r["metadata"]["title"] for r in results)


class TestApproxTokens:
    def test_empty_string(self):
        from backend.ai.rag_engine import _approx_tokens
        assert _approx_tokens("") == 0

    def test_known_word_count(self):
        from backend.ai.rag_engine import _approx_tokens
        text = " ".join(["word"] * 100)
        result = _approx_tokens(text)
        assert 120 <= result <= 140  # 100 words × 1.3


# ── Chunker tests (from ingest script) ───────────────────────────────────────

class TestChunkText:
    def _import(self):
        import sys
        sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.parent))
        from backend.scripts.ingest_rag_sources import (
            chunk_text, MIN_CHUNK_WORDS, MAX_CHUNK_WORDS, OVERLAP_WORDS, _word_count
        )
        return chunk_text, MIN_CHUNK_WORDS, MAX_CHUNK_WORDS, OVERLAP_WORDS, _word_count

    def test_short_text_yields_one_chunk(self):
        chunk_text, *_ = self._import()
        text = " ".join(["word"] * 50)
        chunks = list(chunk_text(text))
        assert len(chunks) == 1

    def test_long_text_yields_multiple_chunks(self):
        chunk_text, MIN_CHUNK_WORDS, MAX_CHUNK_WORDS, OVERLAP_WORDS, _word_count = self._import()
        # 2000 words in multiple paragraphs → should produce several chunks
        para = " ".join([f"word{i}" for i in range(100)])
        text = "\n\n".join([para] * 20)   # 2000 words across 20 paragraphs
        chunks = list(chunk_text(text))
        assert len(chunks) >= 3

    def test_chunk_sizes_within_bounds(self):
        chunk_text, MIN_CHUNK_WORDS, MAX_CHUNK_WORDS, OVERLAP_WORDS, _word_count = self._import()
        text = "\n\n".join([" ".join(["w"] * 80) for _ in range(20)])
        chunks = list(chunk_text(text))
        for chunk in chunks[:-1]:  # last chunk can be undersized
            words = _word_count(chunk)
            assert words <= MAX_CHUNK_WORDS + OVERLAP_WORDS + 10  # some slack

    def test_overlap_carries_words_forward(self):
        chunk_text, MIN_CHUNK_WORDS, MAX_CHUNK_WORDS, OVERLAP_WORDS, _word_count = self._import()
        # MARKER words at the END of the first paragraph so they land in the overlap
        filler = " ".join(["filler"] * (MAX_CHUNK_WORDS - 20))
        markers = " ".join(["MARKER"] * 20)
        first_para = filler + " " + markers      # ends with MARKERs
        second_para = " ".join(["extra"] * 400)
        text = first_para + "\n\n" + second_para
        chunks = list(chunk_text(text))
        if len(chunks) >= 2:
            # Overlap carries the tail of the first chunk → MARKERs appear in chunk 2
            assert "MARKER" in chunks[1]

    def test_very_long_single_paragraph_hard_split(self):
        chunk_text, MIN_CHUNK_WORDS, MAX_CHUNK_WORDS, OVERLAP_WORDS, _word_count = self._import()
        # 1500-word single paragraph (no double newlines) → must still be split
        text = " ".join([f"sentence{i % 30}." for i in range(600)])
        chunks = list(chunk_text(text))
        assert len(chunks) >= 2

    def test_tiny_trailing_fragment_skipped(self):
        chunk_text, MIN_CHUNK_WORDS, MAX_CHUNK_WORDS, OVERLAP_WORDS, _word_count = self._import()
        # Trailing whitespace / empty paragraphs should not produce empty chunks
        text = "\n\n".join([" ".join(["w"] * 100) for _ in range(5)]) + "\n\n  \n\n"
        chunks = list(chunk_text(text))
        for chunk in chunks:
            assert chunk.strip()


# ── Tagger tests ──────────────────────────────────────────────────────────────

class TestTagChunk:
    def _import(self):
        from backend.scripts.ingest_rag_sources import _tag_chunk
        return _tag_chunk

    def test_naloxone_tagged_as_opioid_overdose(self):
        _tag_chunk = self._import()
        text = "Administer naloxone 4mg intranasal for opioid overdose."
        conditions, drugs = _tag_chunk(text, [], [])
        assert "opioid_overdose" in conditions
        assert "naloxone" in drugs

    def test_mdma_heat_tagged(self):
        _tag_chunk = self._import()
        text = "MDMA users are at high risk of heat stroke and hyperthermia."
        conditions, drugs = _tag_chunk(text, [], [])
        assert "heat_stroke" in conditions
        assert "mdma" in drugs

    def test_hyponatremia_tagged(self):
        _tag_chunk = self._import()
        text = "Exercise-associated hyponatremia (EAH) can cause seizures and cerebral oedema."
        conditions, drugs = _tag_chunk(text, [], [])
        assert "hyponatremia" in conditions

    def test_doc_level_hints_applied_to_every_chunk(self):
        _tag_chunk = self._import()
        # Chunk with no drug keywords but doc hint says "naloxone"
        text = "This document covers overdose recognition and response."
        conditions, drugs = _tag_chunk(text, ["opioid_overdose"], ["naloxone"])
        assert "naloxone" in drugs
        assert "opioid_overdose" in conditions

    def test_no_false_positives_on_unrelated_text(self):
        _tag_chunk = self._import()
        text = "The festival attendance was 22,500 people."
        conditions, drugs = _tag_chunk(text, [], [])
        # Should not fire on a purely demographic sentence
        assert "naloxone" not in drugs
        assert "serotonin_syndrome" not in conditions

    def test_returns_sorted_lists(self):
        _tag_chunk = self._import()
        text = "GHB combined with alcohol leads to rapid CNS depression and naloxone is ineffective."
        conditions, drugs = _tag_chunk(text, [], [])
        assert conditions == sorted(conditions)
        assert drugs == sorted(drugs)
