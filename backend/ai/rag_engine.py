"""
RAG engine — SQLite FTS5 backend.
Ingests knowledge chunks from a JSON file and exposes a fast BM25 search.
"""
import json
import os
import sqlite3
from typing import List, Dict, Any, Optional

_DATA_DIR = os.getenv(
    "EVENT_MED_DATA_DIR",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data"),
)
_DB_PATH = os.path.join(_DATA_DIR, "knowledge.sqlite")
_BUNDLED_KB_PATH = os.path.join(_DATA_DIR, "harm_reduction_kb.json")


def _connect() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(_DB_PATH), exist_ok=True)
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE VIRTUAL TABLE IF NOT EXISTS rag_chunks USING fts5(
            collection,
            text,
            metadata,
            chunk_id UNINDEXED,
            tokenize = 'porter unicode61'
        )
        """
    )
    return conn


def _sanitize_fts5_query(text: str) -> str:
    """Convert free text into a safe FTS5 MATCH expression."""
    tokens = []
    for word in text.split():
        clean = "".join(c for c in word if c.isalnum())
        if len(clean) >= 2:
            tokens.append(f'"{clean}"')
    return " OR ".join(tokens) if tokens else '""'


class RAGEngine:
    def __init__(self):
        with _connect() as conn:
            conn.commit()
        self._bootstrap_from_kb()

    def _bootstrap_from_kb(self) -> None:
        """Ingest shipped JSON chunks into FTS5 if the index is empty.
        
        The JSON contains a list of chunks, each with fields:
        {
          "collection": "harm_reduction_protocols" | "substance_database",
          "chunks": [{"id": "...", "text": "...", "metadata": {...}}, ...]
        }
        """
        if not os.path.exists(_BUNDLED_KB_PATH):
            # If the kb file is not written yet, skip for now. It will ingest on first query
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
            
            # Format could be either a single collection or a list of collections
            if isinstance(data, dict) and "collection" in data and "chunks" in data:
                self.add_documents(
                    collection_name=data["collection"],
                    documents=[c["text"] for c in data["chunks"]],
                    metadatas=[c.get("metadata", {}) for c in data["chunks"]],
                    ids=[c["id"] for c in data["chunks"]],
                )
            elif isinstance(data, list):
                for col_data in data:
                    if "collection" in col_data and "chunks" in col_data:
                        self.add_documents(
                            collection_name=col_data["collection"],
                            documents=[c["text"] for c in col_data["chunks"]],
                            metadatas=[c.get("metadata", {}) for c in col_data["chunks"]],
                            ids=[c["id"] for c in col_data["chunks"]],
                        )
        except (json.JSONDecodeError, KeyError, IOError) as e:
            # Skip malformed files silently or log
            print(f"Error bootstrapping RAG: {e}")
            pass

    def query(self, collection_name: str, text: str, k: int = 3) -> List[Dict[str, Any]]:
        fts_query = _sanitize_fts5_query(text)
        chunks: List[Dict[str, Any]] = []
        try:
            with _connect() as conn:
                rows = conn.execute(
                    """
                    SELECT text, metadata
                    FROM rag_chunks
                    WHERE collection = ? AND rag_chunks MATCH ?
                    ORDER BY bm25(rag_chunks)
                    LIMIT ?
                    """,
                    (collection_name, fts_query, k),
                ).fetchall()
            for row in rows:
                try:
                    meta = json.loads(row["metadata"]) if row["metadata"] else {}
                except json.JSONDecodeError:
                    meta = {}
                chunks.append({"text": row["text"], "metadata": meta})
        except sqlite3.OperationalError:
            pass

        return chunks

    def add_documents(
        self,
        collection_name: str,
        documents: List[str],
        metadatas: List[dict],
        ids: List[str],
    ) -> None:
        with _connect() as conn:
            for doc, meta, chunk_id in zip(documents, metadatas, ids):
                conn.execute("DELETE FROM rag_chunks WHERE chunk_id = ?", (chunk_id,))
                conn.execute(
                    "INSERT INTO rag_chunks (collection, text, metadata, chunk_id) VALUES (?, ?, ?, ?)",
                    (collection_name, doc, json.dumps(meta or {}), chunk_id),
                )
            conn.commit()

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
