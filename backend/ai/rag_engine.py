"""
RAG engine — SQLite FTS5 backend.

Schema v2 adds:
  - drugs_tagged  : space-separated drug names, FTS5-indexed for exact-match boost
  - condition_tags: space-separated condition labels, FTS5-indexed
  - source_url    : stored inside metadata JSON (not a separate column)
  - source_tier   : stored inside metadata JSON

hybrid_query() merges BM25 full-text results with an exact-match drug-name boost
and enforces a ~3 000-token context cap so Gemma 3 4B sees the best chunks only.

Token budget: approximate as words × 1.3 (conservative for medical text).
"""
import json
import os
import re
import sqlite3
from typing import Any, Dict, List, Optional

_DATA_DIR = os.getenv(
    "EVENT_MED_DATA_DIR",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data"),
)
_DB_PATH = os.path.join(_DATA_DIR, "knowledge.sqlite")
_BUNDLED_KB_PATH = os.path.abspath(
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "harm_reduction_kb.json")
)

# Schema version stored as a plain row in a tiny bookkeeping table
_SCHEMA_VERSION = 2

# Token cap for total retrieved context passed to the LLM.
# Gemma 3 4B degrades on very long contexts; 3 000 tokens ≈ 2 300 words.
MAX_CONTEXT_TOKENS = 3_000
_WORDS_PER_TOKEN = 1.3  # conservative for medical prose


def _approx_tokens(text: str) -> int:
    return int(len(text.split()) * _WORDS_PER_TOKEN)


def _sanitize_fts5_query(text: str) -> str:
    """Convert free text into a safe FTS5 MATCH expression (OR of quoted terms)."""
    tokens = []
    for word in text.split():
        clean = re.sub(r"[^\w]", "", word)
        if len(clean) >= 2:
            tokens.append(f'"{clean}"')
    return " OR ".join(tokens) if tokens else '""'


def _connect() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(_DB_PATH), exist_ok=True)
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_schema(conn: sqlite3.Connection) -> None:
    """Create tables or migrate from v1 (no drugs_tagged / condition_tags columns)."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS _schema_meta (
            key   TEXT PRIMARY KEY,
            value TEXT
        )
        """
    )
    row = conn.execute(
        "SELECT value FROM _schema_meta WHERE key = 'version'"
    ).fetchone()
    current_version = int(row["value"]) if row else 1

    if current_version < _SCHEMA_VERSION:
        # Drop old FTS5 table and recreate; data is re-ingestible from KB files.
        conn.execute("DROP TABLE IF EXISTS rag_chunks")
        conn.execute(
            "INSERT OR REPLACE INTO _schema_meta (key, value) VALUES ('version', ?)",
            (str(_SCHEMA_VERSION),),
        )

    conn.execute(
        """
        CREATE VIRTUAL TABLE IF NOT EXISTS rag_chunks USING fts5(
            collection,
            text,
            metadata,
            drugs_tagged,
            condition_tags,
            chunk_id    UNINDEXED,
            tokenize = 'porter unicode61'
        )
        """
    )
    conn.commit()


class RAGEngine:
    def __init__(self):
        with _connect() as conn:
            _ensure_schema(conn)
        self._bootstrap_from_kb()

    # ── Ingestion ─────────────────────────────────────────────────────────────

    def _bootstrap_from_kb(self) -> None:
        """Ingest shipped harm_reduction_kb.json if the index is empty."""
        if not os.path.exists(_BUNDLED_KB_PATH):
            return
        try:
            with _connect() as conn:
                existing = conn.execute("SELECT count(*) FROM rag_chunks").fetchone()[0]
            if existing > 0:
                return
        except sqlite3.OperationalError:
            return

        try:
            with open(_BUNDLED_KB_PATH, encoding="utf-8") as f:
                data = json.load(f)

            collections = (
                [data] if isinstance(data, dict) and "collection" in data
                else data if isinstance(data, list)
                else []
            )
            for col_data in collections:
                if "collection" not in col_data or "chunks" not in col_data:
                    continue
                self.add_documents(
                    collection_name=col_data["collection"],
                    documents=[c["text"] for c in col_data["chunks"]],
                    metadatas=[c.get("metadata", {}) for c in col_data["chunks"]],
                    ids=[c["id"] for c in col_data["chunks"]],
                )
        except (json.JSONDecodeError, KeyError, IOError) as exc:
            print(f"[RAGEngine] bootstrap error: {exc}")

    def add_documents(
        self,
        collection_name: str,
        documents: List[str],
        metadatas: List[dict],
        ids: List[str],
    ) -> None:
        with _connect() as conn:
            _ensure_schema(conn)
            for doc, meta, chunk_id in zip(documents, metadatas, ids):
                drugs = meta.get("drugs_tagged", [])
                conditions = meta.get("condition_tags", [])
                drugs_str = " ".join(drugs) if isinstance(drugs, list) else str(drugs)
                cond_str = " ".join(conditions) if isinstance(conditions, list) else str(conditions)

                conn.execute("DELETE FROM rag_chunks WHERE chunk_id = ?", (chunk_id,))
                conn.execute(
                    """
                    INSERT INTO rag_chunks
                        (collection, text, metadata, drugs_tagged, condition_tags, chunk_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        collection_name,
                        doc,
                        json.dumps(meta or {}),
                        drugs_str,
                        cond_str,
                        chunk_id,
                    ),
                )
            conn.commit()

    # ── Retrieval ─────────────────────────────────────────────────────────────

    def query(
        self,
        collection_name: str,
        text: str,
        k: int = 4,
    ) -> List[Dict[str, Any]]:
        """BM25 full-text search — backward-compatible public API."""
        return self.hybrid_query(
            collection_name=collection_name,
            text=text,
            drug_names=None,
            k=k,
        )

    def hybrid_query(
        self,
        collection_name: str,
        text: str,
        drug_names: Optional[List[str]] = None,
        k: int = 6,
        max_context_tokens: int = MAX_CONTEXT_TOKENS,
    ) -> List[Dict[str, Any]]:
        """
        Two-stage hybrid retrieval:

        Stage 1 — BM25 full-text search across all FTS5 columns (text, drugs_tagged,
                   condition_tags) using porter stemming. Returns up to k*2 candidates.

        Stage 2 — Exact-match drug-name boost: any chunk whose drugs_tagged contains
                   one of the requested drug names moves to the front of the list.

        Post-filter — Enforce max_context_tokens budget: iterate ranked results and
                      stop adding chunks when the cumulative token count would exceed
                      the cap. Always include at least one chunk regardless of length.

        Returns: list of {text, metadata} dicts, best first.
        """
        fts_query = _sanitize_fts5_query(text)
        candidates: List[Dict[str, Any]] = []
        boosted_ids: set[str] = set()

        try:
            with _connect() as conn:
                # Stage 1: BM25
                rows = conn.execute(
                    """
                    SELECT chunk_id, text, metadata, drugs_tagged, condition_tags
                    FROM rag_chunks
                    WHERE collection = ? AND rag_chunks MATCH ?
                    ORDER BY bm25(rag_chunks)
                    LIMIT ?
                    """,
                    (collection_name, fts_query, k * 2),
                ).fetchall()

                for row in rows:
                    try:
                        meta = json.loads(row["metadata"]) if row["metadata"] else {}
                    except json.JSONDecodeError:
                        meta = {}
                    candidates.append({
                        "chunk_id": row["chunk_id"],
                        "text": row["text"],
                        "metadata": meta,
                        "drugs_tagged": row["drugs_tagged"] or "",
                    })

                # Stage 2: drug-name exact-match boost
                if drug_names:
                    for drug in drug_names:
                        drug_clean = drug.lower().strip()
                        if not drug_clean:
                            continue
                        boost_rows = conn.execute(
                            """
                            SELECT chunk_id FROM rag_chunks
                            WHERE collection = ? AND drugs_tagged MATCH ?
                            LIMIT ?
                            """,
                            (collection_name, f'"{drug_clean}"', k),
                        ).fetchall()
                        for r in boost_rows:
                            boosted_ids.add(r["chunk_id"])

        except sqlite3.OperationalError:
            return []

        # Re-rank: boosted chunks first, then BM25 order
        boosted = [c for c in candidates if c["chunk_id"] in boosted_ids]
        rest = [c for c in candidates if c["chunk_id"] not in boosted_ids]
        ranked = boosted + rest

        # Enforce token budget — always return at least 1 result
        results: List[Dict[str, Any]] = []
        token_total = 0
        for item in ranked:
            chunk_tokens = _approx_tokens(item["text"])
            if results and token_total + chunk_tokens > max_context_tokens:
                break
            results.append({"text": item["text"], "metadata": item["metadata"]})
            token_total += chunk_tokens
            if len(results) >= k:
                break

        return results

    # ── Stats ──────────────────────────────────────────────────────────────────

    def collection_stats(self, collection_name: str) -> int:
        try:
            with _connect() as conn:
                row = conn.execute(
                    "SELECT count(*) FROM rag_chunks WHERE collection = ?",
                    (collection_name,),
                ).fetchone()
                return row[0] if row else 0
        except sqlite3.OperationalError:
            return 0

    def all_collection_stats(self) -> Dict[str, int]:
        """Return row counts for every collection in the index."""
        try:
            with _connect() as conn:
                rows = conn.execute(
                    "SELECT collection, count(*) as cnt FROM rag_chunks GROUP BY collection"
                ).fetchall()
                return {r["collection"]: r["cnt"] for r in rows}
        except sqlite3.OperationalError:
            return {}
