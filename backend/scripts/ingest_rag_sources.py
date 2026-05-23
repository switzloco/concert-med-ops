"""
Concert Med Ops — Tier-1 RAG Corpus Ingestion Script
=====================================================

Downloads the five authoritative Tier-1 sources, extracts clean text,
chunks at 400–700 tokens with 80–120 token overlap, tags each chunk with
condition_tags[] and drugs_tagged[], and writes everything into the SQLite
FTS5 knowledge store used by the backend RAG engine.

Requirements (already in backend/requirements.txt):
  pip install pymupdf trafilatura httpx

Usage:
  # Ingest all sources:
  python -m backend.scripts.ingest_rag_sources

  # Ingest only one source by key:
  python -m backend.scripts.ingest_rag_sources --source who_mass_gatherings

  # Point at a manually-downloaded PDF (bypass URL fetch):
  python -m backend.scripts.ingest_rag_sources --source samhsa_overdose_toolkit \
      --local-pdf /path/to/downloaded.pdf

  # Dry-run (print chunk stats, don't write to DB):
  python -m backend.scripts.ingest_rag_sources --dry-run

Sources ingested:
  - WHO Public Health for Mass Gatherings 2015   (CC BY-NC-SA 3.0 IGO)
  - SAMHSA Overdose Prevention & Response Toolkit 2024 (Public Domain)
  - EMCrit IBCC — 8 selected toxicology chapters (copyrighted, free-to-read)
  - WMS Exercise-Associated Hyponatremia 2020   (copyrighted, free PDF mirrors)
  - ACEP Hyperactive Delirium Clinical Policy 2021 + ACMT 2023 (copyrighted, free)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator, Optional

# ── path setup ───────────────────────────────────────────────────────────────
_REPO_ROOT = Path(__file__).parent.parent.parent
_DATA_DIR = Path(os.getenv("EVENT_MED_DATA_DIR", str(_REPO_ROOT / "backend" / "data")))
_SOURCES_DIR = _DATA_DIR / "sources"
_PDFS_DIR = _SOURCES_DIR / "pdfs"
_PDFS_DIR.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(_REPO_ROOT))

# ── Token budget constants (must match rag_engine.py) ────────────────────────
TARGET_CHUNK_TOKENS = 550   # mid-point of 400–700 range
MIN_CHUNK_TOKENS = 400
MAX_CHUNK_TOKENS = 700
OVERLAP_TOKENS = 100        # carry-forward to maintain context continuity
WORDS_PER_TOKEN = 1.3       # approximate for medical prose

TARGET_CHUNK_WORDS = int(TARGET_CHUNK_TOKENS / WORDS_PER_TOKEN)   # ~423
MIN_CHUNK_WORDS = int(MIN_CHUNK_TOKENS / WORDS_PER_TOKEN)         # ~307
MAX_CHUNK_WORDS = int(MAX_CHUNK_TOKENS / WORDS_PER_TOKEN)         # ~538
OVERLAP_WORDS = int(OVERLAP_TOKENS / WORDS_PER_TOKEN)             # ~76


# ── Keyword taxonomies for tagging ───────────────────────────────────────────

CONDITION_KEYWORDS: dict[str, list[str]] = {
    "serotonin_syndrome": [
        "serotonin syndrome", "hunter criteria", "hunter toxicity", "clonus",
        "hyperreflexia", "serotonergic", "serotonin toxicity",
    ],
    "heat_stroke": [
        "heat stroke", "hyperthermia", "active cooling", "exertional heat",
        "rectal temperature", "cold water immersion", "evaporative cooling",
        "heat illness", "heat injury",
    ],
    "opioid_overdose": [
        "naloxone", "narcan", "opioid overdose", "respiratory depression",
        "pinpoint pupils", "fentanyl overdose", "heroin overdose",
        "opioid reversal", "nalmefene",
    ],
    "hyponatremia": [
        "hyponatremia", "exercise-associated hyponatremia", "eah",
        "siadh", "overhydration", "hypertonic saline", "sodium deficiency",
        "water intoxication", "electrolyte", "serum sodium",
    ],
    "rhabdomyolysis": [
        "rhabdomyolysis", "myoglobin", "myoglobinuria", "creatine kinase",
        "dark urine", "muscle breakdown", "ck elevation", "cola-colored urine",
    ],
    "ghb_intoxication": [
        "ghb", "gamma-hydroxybutyrate", "recovery position", "ghb coma",
        "ghb overdose", "gbl",
    ],
    "agitation": [
        "agitation", "excited delirium", "hyperactive delirium",
        "chemical sedation", "sympathomimetic toxicity", "excited state",
        "acute behavioral disturbance",
    ],
    "triage_mci": [
        "start triage", "salt triage", "mass casualty", "mci",
        "triage category", "tag color", "immediate", "delayed", "expectant",
        "simple triage",
    ],
    "opioid_treatment": [
        "methadone", "buprenorphine", "suboxone", "naltrexone",
        "medication-assisted treatment", "mat", "medications for opioid use disorder", "moud",
    ],
    "withdrawal": [
        "withdrawal", "detoxification", "delirium tremens", "alcohol withdrawal",
        "opioid withdrawal", "stimulant withdrawal",
    ],
    "harm_reduction": [
        "harm reduction", "reagent test", "drug checking", "fentanyl strip",
        "test strip", "dancesafe", "energy control",
    ],
    "transport": [
        "hospital transport", "ambulance", "ems transport", "air transport",
        "trauma level", "level 1 trauma", "hospital diversion",
    ],
    "mass_gathering_ops": [
        "mass gathering", "festival medical", "event medicine",
        "medical command", "incident command", "command structure",
        "medical planning", "ambulance coverage",
    ],
}

DRUG_KEYWORDS: dict[str, list[str]] = {
    "mdma": ["mdma", "ecstasy", "molly", "methylenedioxymethamphetamine"],
    "ketamine": ["ketamine", "special k", "dissociative anesthetic"],
    "ghb": ["ghb", "gamma-hydroxybutyrate", "gamma hydroxy"],
    "gbl": ["gbl", "gamma-butyrolactone"],
    "fentanyl": ["fentanyl", "fentanil", "carfentanil"],
    "heroin": ["heroin", "diacetylmorphine"],
    "opioid": ["opioid", "opiate", "morphine", "oxycodone", "hydrocodone"],
    "naloxone": ["naloxone", "narcan"],
    "nalmefene": ["nalmefene"],
    "alcohol": ["alcohol", "ethanol", "ethyl alcohol"],
    "cocaine": ["cocaine", "crack cocaine"],
    "methamphetamine": ["methamphetamine", "meth", "crystal meth"],
    "amphetamine": ["amphetamine", "adderall", "dextroamphetamine"],
    "lsd": ["lsd", "lysergic acid", "acid", "lysergide"],
    "psilocybin": ["psilocybin", "mushrooms", "magic mushrooms", "psilocin"],
    "cannabis": ["cannabis", "marijuana", "thc", "cbd"],
    "benzodiazepines": ["benzodiazepine", "midazolam", "diazepam", "lorazepam"],
    "ssri": ["ssri", "sertraline", "fluoxetine", "paroxetine", "escitalopram", "citalopram"],
    "maoi": ["maoi", "monoamine oxidase", "phenelzine", "tranylcypromine"],
    "xylazine": ["xylazine", "tranq"],
    "nbomes": ["nbome", "25i-nbome", "n-bomb"],
    "kratom": ["kratom", "mitragynine"],
}


# ── Source definitions ────────────────────────────────────────────────────────

@dataclass
class Source:
    key: str
    title: str
    collection: str
    source_type: str          # "pdf" | "html"
    url: str
    licence: str
    tier: int
    condition_hints: list[str] = field(default_factory=list)  # extra tags for whole doc
    drug_hints: list[str] = field(default_factory=list)
    alt_urls: list[str] = field(default_factory=list)


TIER1_SOURCES: list[Source] = [
    Source(
        key="who_mass_gatherings",
        title="WHO Public Health for Mass Gatherings: Key Considerations (2015)",
        collection="mass_gathering_protocols",
        source_type="pdf",
        url="https://iris.who.int/bitstream/handle/10665/162109/WHO_HSE_GCR_2015.5_eng.pdf",
        alt_urls=[
            "https://apps.who.int/iris/bitstream/handle/10665/162109/WHO_HSE_GCR_2015.5_eng.pdf",
        ],
        licence="CC BY-NC-SA 3.0 IGO",
        tier=1,
        condition_hints=["mass_gathering_ops", "triage_mci", "transport"],
    ),
    Source(
        key="samhsa_overdose_toolkit",
        title="SAMHSA Overdose Prevention and Response Toolkit (PEP23-03-00-001, 2024)",
        collection="harm_reduction_protocols",
        source_type="pdf",
        url="https://library.samhsa.gov/sites/default/files/overdose-prevention-response-kit-pep23-03-00-001.pdf",
        licence="Public Domain (US Federal Work)",
        tier=1,
        condition_hints=["opioid_overdose"],
        drug_hints=["naloxone", "opioid", "fentanyl", "nalmefene"],
    ),
    Source(
        key="wms_eah_2020",
        title="Wilderness Medical Society Clinical Practice Guidelines for Exercise-Associated Hyponatremia (2020)",
        collection="harm_reduction_protocols",
        source_type="pdf",
        url="https://www.wildmedcenter.com/uploads/5/9/8/2/5982510/wms_exercise-associated_hyponatremia_2020.pdf",
        alt_urls=[
            "https://emergencymedicinecases.com/wp-content/uploads/filebase/pdf/Guidelines-EAH.pdf",
        ],
        licence="Copyrighted — Elsevier/WMS; free PDFs on author mirror sites",
        tier=1,
        condition_hints=["hyponatremia"],
        drug_hints=["mdma"],
    ),
    Source(
        key="acep_hyperactive_delirium",
        title="ACEP Clinical Policy: Critical Issues in the Evaluation and Management of Adult Patients Presenting with Hyperactive Delirium (2021)",
        collection="harm_reduction_protocols",
        source_type="pdf",
        url="https://www.acep.org/siteassets/new-pdfs/clinical-policies/severe-agitation-cp.pdf",
        licence="Copyrighted — ACEP; free to read",
        tier=1,
        condition_hints=["agitation"],
        drug_hints=["mdma", "cocaine", "methamphetamine", "benzodiazepines"],
    ),
    Source(
        key="acmt_end_excited_delirium",
        title="ACMT Position Statement: End the Use of the Term 'Excited Delirium' (2023)",
        collection="harm_reduction_protocols",
        source_type="pdf",
        url="https://www.acmt.net/wp-content/uploads/2023/05/PS_230501_End-the-Use-of-the-Term-Excited-Delirium.pdf",
        licence="Copyrighted — ACMT; free to read",
        tier=1,
        condition_hints=["agitation"],
        drug_hints=["cocaine", "methamphetamine"],
    ),
    Source(
        key="chemm_salt_triage",
        title="HHS CHEMM: SALT Mass-Casualty Triage Algorithm",
        collection="mass_gathering_protocols",
        source_type="html",
        url="https://chemm.hhs.gov/salttriage.htm",
        licence="Public Domain (US Federal Work)",
        tier=1,
        condition_hints=["triage_mci", "mass_gathering_ops"],
    ),
    Source(
        key="chemm_start_triage",
        title="HHS CHEMM: START Adult Triage Algorithm",
        collection="mass_gathering_protocols",
        source_type="html",
        url="https://chemm.hhs.gov/startadult.htm",
        licence="Public Domain (US Federal Work)",
        tier=1,
        condition_hints=["triage_mci", "mass_gathering_ops"],
    ),
]

TIER2_SOURCES: list[Source] = [
    Source(
        key="who_opioid_overdose_mgmt",
        title="WHO Community Management of Opioid Overdose (2014)",
        collection="harm_reduction_protocols",
        source_type="html",
        url="https://www.ncbi.nlm.nih.gov/books/NBK264295/",
        licence="CC BY-NC-SA 3.0 IGO",
        tier=2,
        condition_hints=["opioid_overdose"],
        drug_hints=["naloxone", "opioid", "heroin"],
    ),
    Source(
        key="emcrit_serotonin_syndrome",
        title="EMCrit IBCC: Serotonin Syndrome",
        collection="harm_reduction_protocols",
        source_type="html",
        url="https://emcrit.org/ibcc/serotonin/",
        licence="Copyrighted — EMCrit; free to read",
        tier=2,
        condition_hints=["serotonin_syndrome"],
        drug_hints=["mdma", "ssri", "maoi"],
    ),
    Source(
        key="emcrit_sympathomimetic",
        title="EMCrit IBCC: Sympathomimetic Toxicity",
        collection="harm_reduction_protocols",
        source_type="html",
        url="https://emcrit.org/ibcc/symp/",
        licence="Copyrighted — EMCrit; free to read",
        tier=2,
        condition_hints=["agitation", "heat_stroke"],
        drug_hints=["cocaine", "methamphetamine", "mdma", "amphetamine"],
    ),
    Source(
        key="emcrit_opioid_intoxication",
        title="EMCrit IBCC: Opioid Intoxication",
        collection="harm_reduction_protocols",
        source_type="html",
        url="https://emcrit.org/ibcc/opioid/",
        licence="Copyrighted — EMCrit; free to read",
        tier=2,
        condition_hints=["opioid_overdose"],
        drug_hints=["opioid", "fentanyl", "naloxone", "heroin"],
    ),
    Source(
        key="emcrit_ghb",
        title="EMCrit IBCC: GHB / GBL Intoxication",
        collection="harm_reduction_protocols",
        source_type="html",
        url="https://emcrit.org/ibcc/ghb/",
        licence="Copyrighted — EMCrit; free to read",
        tier=2,
        condition_hints=["ghb_intoxication"],
        drug_hints=["ghb", "gbl", "alcohol"],
    ),
    Source(
        key="emcrit_rhabdomyolysis",
        title="EMCrit IBCC: Rhabdomyolysis",
        collection="harm_reduction_protocols",
        source_type="html",
        url="https://emcrit.org/ibcc/rhabdo/",
        licence="Copyrighted — EMCrit; free to read",
        tier=2,
        condition_hints=["rhabdomyolysis"],
        drug_hints=["mdma", "cocaine", "methamphetamine"],
    ),
    Source(
        key="emcrit_hyperthermia",
        title="EMCrit IBCC: Hyperthermia and Heat Stroke",
        collection="harm_reduction_protocols",
        source_type="html",
        url="https://emcrit.org/ibcc/heat/",
        licence="Copyrighted — EMCrit; free to read",
        tier=2,
        condition_hints=["heat_stroke"],
        drug_hints=["mdma", "cocaine"],
    ),
    Source(
        key="emcrit_hyponatremia",
        title="EMCrit IBCC: Hyponatremia",
        collection="harm_reduction_protocols",
        source_type="html",
        url="https://emcrit.org/ibcc/hyponatremia/",
        licence="Copyrighted — EMCrit; free to read",
        tier=2,
        condition_hints=["hyponatremia"],
        drug_hints=["mdma"],
    ),
]

ALL_SOURCES: dict[str, Source] = {s.key: s for s in TIER1_SOURCES + TIER2_SOURCES}


# ── Text extraction ───────────────────────────────────────────────────────────

def _fetch_pdf(url: str, alt_urls: list[str], dest_path: Path) -> Optional[Path]:
    """Download a PDF, trying alt_urls on 4xx/5xx. Returns path or None."""
    try:
        import httpx
    except ImportError:
        print("  ✗ httpx not installed — run: pip install httpx")
        return None

    for attempt_url in [url] + alt_urls:
        try:
            print(f"  Fetching PDF: {attempt_url}")
            with httpx.Client(follow_redirects=True, timeout=60) as client:
                r = client.get(attempt_url, headers={"User-Agent": "ConcertMedOps/1.0 (research)"})
            if r.status_code == 200 and b"%PDF" in r.content[:10]:
                dest_path.write_bytes(r.content)
                print(f"  ✓ Downloaded ({len(r.content) / 1024:.0f} KB) → {dest_path.name}")
                return dest_path
            else:
                print(f"  ✗ HTTP {r.status_code} from {attempt_url}")
        except Exception as exc:
            print(f"  ✗ Error fetching {attempt_url}: {exc}")
    return None


def _extract_pdf_pages(pdf_path: Path) -> list[tuple[int, str]]:
    """
    Extract text per page from a PDF using PyMuPDF.

    Returns a list of (1-based page_number, page_text) tuples so the
    chunker can track which source page each chunk starts and ends on.
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        print("  ✗ pymupdf not installed — run: pip install pymupdf")
        return []

    doc = fitz.open(str(pdf_path))
    pages: list[tuple[int, str]] = []
    for page in doc:
        text = page.get_text("text")
        text = text.replace("ﬁ", "fi").replace("ﬂ", "fl").replace("\xad", "")
        text = text.strip()
        if text:
            pages.append((page.number + 1, text))  # 1-based
    doc.close()
    return pages


def _fetch_html_sections(url: str) -> list[tuple[str, str]]:
    """
    Fetch an HTML page and split it into (section_heading, section_text) pairs.

    trafilatura returns plain text with Markdown-style headings when
    include_formatting=True. We split on heading lines (# / ## / ###) so each
    section carries its heading as metadata.  Falls back to a single
    (title, full_text) pair when no headings are detected.
    """
    try:
        import trafilatura
    except ImportError:
        print("  ✗ trafilatura not installed — run: pip install trafilatura")
        return []

    try:
        print(f"  Fetching HTML: {url}")
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            print(f"  ✗ trafilatura could not fetch {url}")
            return []
        text = trafilatura.extract(
            downloaded,
            include_tables=True,
            include_formatting=True,
            no_fallback=False,
        )
        if not text:
            print(f"  ✗ trafilatura extracted no content from {url}")
            return []

        print(f"  ✓ Extracted {len(text.split()):,} words")

        # Split on Markdown headings
        heading_pattern = re.compile(r"^(#{1,3})\s+(.+)$", re.MULTILINE)
        matches = list(heading_pattern.finditer(text))

        if not matches:
            return [("Main Content", text)]

        sections: list[tuple[str, str]] = []
        # Text before the first heading
        preamble = text[: matches[0].start()].strip()
        if preamble:
            sections.append(("Introduction", preamble))

        for i, m in enumerate(matches):
            heading = m.group(2).strip()
            body_start = m.end()
            body_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            body = text[body_start:body_end].strip()
            if body:
                sections.append((heading, body))

        return sections

    except Exception as exc:
        print(f"  ✗ Error fetching HTML {url}: {exc}")
        return []


# ── Chunking ──────────────────────────────────────────────────────────────────

PagedChunk = tuple[str, int, int]  # (text, page_start, page_end)


def _split_into_paragraphs(text: str) -> list[str]:
    """Split text into coarse semantic units (double-newline paragraphs, numbered items)."""
    # Normalise whitespace
    text = re.sub(r"\r\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Split on double newlines and also on numbered list items at start of line
    paragraphs = re.split(r"\n\n+|\n(?=\d+\.|\s*[-•]\s)", text)
    return [p.strip() for p in paragraphs if p.strip()]


def _word_count(text: str) -> int:
    return len(text.split())


def chunk_text(text: str) -> Iterator[str]:
    """
    Yield overlapping chunks of approximately TARGET_CHUNK_WORDS words.

    Algorithm:
      1. Split into paragraphs.
      2. Greedily accumulate paragraphs until MAX_CHUNK_WORDS is reached.
      3. Emit the accumulated buffer as one chunk.
      4. Carry the last OVERLAP_WORDS words forward into the next chunk.
      5. Very long paragraphs (> MAX_CHUNK_WORDS) are hard-split at sentence boundaries.
    """
    paragraphs = _split_into_paragraphs(text)
    buffer: list[str] = []
    buf_words = 0

    for para in paragraphs:
        para_words = _word_count(para)

        # Hard-split single overly-long paragraphs
        if para_words > MAX_CHUNK_WORDS:
            sentences = re.split(r"(?<=[.!?])\s+", para)
            # Fallback: if no sentence boundaries, split on word boundaries
            if len(sentences) <= 1:
                words = para.split()
                sentences = [
                    " ".join(words[i: i + MAX_CHUNK_WORDS])
                    for i in range(0, len(words), MAX_CHUNK_WORDS - OVERLAP_WORDS)
                ]
            sub_buf: list[str] = []
            sub_words = 0
            for sent in sentences:
                sw = _word_count(sent)
                if sub_words + sw > MAX_CHUNK_WORDS and sub_buf:
                    yield " ".join(sub_buf)
                    # Carry overlap forward
                    all_words = " ".join(sub_buf).split()
                    carry = " ".join(all_words[-OVERLAP_WORDS:])
                    sub_buf = [carry] if carry else []
                    sub_words = _word_count(carry)
                sub_buf.append(sent)
                sub_words += sw
            if sub_buf:
                para = " ".join(sub_buf)
                para_words = _word_count(para)

        if buf_words + para_words > MAX_CHUNK_WORDS and buf_words >= MIN_CHUNK_WORDS:
            yield "\n\n".join(buffer)
            # Overlap: keep the last OVERLAP_WORDS from the buffer
            all_words = "\n\n".join(buffer).split()
            carry = " ".join(all_words[-OVERLAP_WORDS:])
            buffer = [carry] if carry else []
            buf_words = _word_count(carry)

        buffer.append(para)
        buf_words += para_words

    if buffer and buf_words >= 20:  # skip tiny trailing fragments
        yield "\n\n".join(buffer)


def chunk_paged_text(pages: list[tuple[int, str]]) -> Iterator[PagedChunk]:
    """
    Page-aware chunker for PDF content.

    Takes a list of (page_num, page_text) pairs and yields
    (chunk_text, page_start, page_end) tuples.  Each chunk records the
    first and last PDF page it spans so medics can look up the source.
    """
    # Build a flat list of (page_num, paragraph) pairs
    tagged_paras: list[tuple[int, str]] = []
    for page_num, page_text in pages:
        for para in _split_into_paragraphs(page_text):
            tagged_paras.append((page_num, para))

    if not tagged_paras:
        return

    buffer: list[str] = []
    buf_words = 0
    page_start = tagged_paras[0][0]
    page_end = tagged_paras[0][0]

    def _emit() -> PagedChunk:
        return ("\n\n".join(buffer), page_start, page_end)

    for page_num, para in tagged_paras:
        para_words = _word_count(para)

        # Hard-split overly long paragraphs (same logic as chunk_text)
        if para_words > MAX_CHUNK_WORDS:
            sentences = re.split(r"(?<=[.!?])\s+", para)
            if len(sentences) <= 1:
                words = para.split()
                sentences = [
                    " ".join(words[i: i + MAX_CHUNK_WORDS])
                    for i in range(0, len(words), MAX_CHUNK_WORDS - OVERLAP_WORDS)
                ]
            sub_buf: list[str] = []
            sub_words = 0
            for sent in sentences:
                sw = _word_count(sent)
                if sub_words + sw > MAX_CHUNK_WORDS and sub_buf:
                    yield " ".join(sub_buf), page_num, page_num
                    all_words = " ".join(sub_buf).split()
                    carry = " ".join(all_words[-OVERLAP_WORDS:])
                    sub_buf = [carry] if carry else []
                    sub_words = _word_count(carry)
                sub_buf.append(sent)
                sub_words += sw
            if sub_buf:
                para = " ".join(sub_buf)
                para_words = _word_count(para)

        if buf_words + para_words > MAX_CHUNK_WORDS and buf_words >= MIN_CHUNK_WORDS:
            yield _emit()
            all_words = "\n\n".join(buffer).split()
            carry = " ".join(all_words[-OVERLAP_WORDS:])
            buffer = [carry] if carry else []
            buf_words = _word_count(carry)
            page_start = page_num  # reset; carry may span pages

        buffer.append(para)
        buf_words += para_words
        page_end = page_num  # track last page seen in this buffer

    if buffer and buf_words >= 20:
        yield _emit()


def chunk_html_section(section_text: str, section_heading: str) -> Iterator[tuple[str, str]]:
    """
    Chunk a single HTML section, yielding (chunk_text, section_heading) pairs.
    All chunks from the same section share the same heading metadata.
    """
    for chunk in chunk_text(section_text):
        yield chunk, section_heading


# ── Tagging ───────────────────────────────────────────────────────────────────

def _tag_chunk(
    text: str,
    doc_condition_hints: list[str],
    doc_drug_hints: list[str],
) -> tuple[list[str], list[str]]:
    """
    Return (condition_tags, drugs_tagged) for a single chunk.

    Keyword matching is case-insensitive.  doc_*_hints inject document-level
    signals so every chunk from (e.g.) the WMS hyponatremia PDF inherits
    "hyponatremia" even if the word appears only in the title.
    """
    text_lower = text.lower()

    conditions: set[str] = set(doc_condition_hints)
    for cond, keywords in CONDITION_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            conditions.add(cond)

    drugs: set[str] = set(doc_drug_hints)
    for drug_name, keywords in DRUG_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            drugs.add(drug_name)

    return sorted(conditions), sorted(drugs)


# ── Chunk ID generation ───────────────────────────────────────────────────────

def _chunk_id(source_key: str, idx: int, text: str) -> str:
    """Stable chunk ID: source key + index + hash of first 64 chars."""
    prefix = text[:64].encode("utf-8")
    digest = hashlib.md5(prefix).hexdigest()[:8]
    return f"{source_key}-{idx:04d}-{digest}"


# ── Ingestion pipeline ────────────────────────────────────────────────────────

def ingest_source(
    source: Source,
    local_pdf: Optional[Path] = None,
    dry_run: bool = False,
) -> dict:
    """
    Full pipeline for one source: fetch → extract → chunk → tag → write.

    Returns a stats dict: {source_key, chunks_written, total_words, skipped}.
    """
    print(f"\n{'─'*60}")
    print(f"Source: {source.title}")
    print(f"  Collection: {source.collection} | Tier: {source.tier}")
    print(f"  Licence: {source.licence}")

    # ── Fetch / extract ───────────────────────────────────────────────────────
    # pdf_pages: list[(page_num, text)]  — populated for PDF sources
    # html_sections: list[(heading, text)] — populated for HTML sources
    pdf_pages: list[tuple[int, str]] = []
    html_sections: list[tuple[str, str]] = []
    total_words = 0

    if source.source_type == "pdf":
        pdf_path = local_pdf or (_PDFS_DIR / f"{source.key}.pdf")
        if pdf_path.exists():
            print(f"  Using cached PDF: {pdf_path}")
        else:
            fetched = _fetch_pdf(source.url, source.alt_urls, pdf_path)
            if not fetched:
                print(f"  ✗ SKIPPED — could not fetch. Download manually to {pdf_path}")
                return {"source_key": source.key, "chunks_written": 0, "total_words": 0, "skipped": True}

        pdf_pages = _extract_pdf_pages(pdf_path)
        total_words = sum(_word_count(t) for _, t in pdf_pages)
        if not pdf_pages:
            print(f"  ✗ SKIPPED — extracted text is empty")
            return {"source_key": source.key, "chunks_written": 0, "total_words": 0, "skipped": True}
        print(f"  Extracted {total_words:,} words across {len(pdf_pages)} pages")

    elif source.source_type == "html":
        html_sections = _fetch_html_sections(source.url)
        if not html_sections:
            print(f"  ✗ SKIPPED — could not extract content from {source.url}")
            return {"source_key": source.key, "chunks_written": 0, "total_words": 0, "skipped": True}
        total_words = sum(_word_count(t) for _, t in html_sections)
        print(f"  Extracted {total_words:,} words across {len(html_sections)} sections")

    # ── Chunk ─────────────────────────────────────────────────────────────────
    # raw_chunks: list of dicts with keys text, page_start (or section_heading)
    raw_chunks: list[dict] = []

    if pdf_pages:
        for chunk_text_val, page_start, page_end in chunk_paged_text(pdf_pages):
            raw_chunks.append({
                "text": chunk_text_val,
                "page_start": page_start,
                "page_end": page_end,
                "section": None,
            })
    else:
        for heading, section_body in html_sections:
            for chunk_text_val, section_heading in chunk_html_section(section_body, heading):
                raw_chunks.append({
                    "text": chunk_text_val,
                    "page_start": None,
                    "page_end": None,
                    "section": section_heading,
                })

    print(f"  Produced {len(raw_chunks)} chunks (~{TARGET_CHUNK_TOKENS} tokens each)")

    if dry_run:
        sizes = [_word_count(c["text"]) for c in raw_chunks]
        if sizes:
            print(f"  [DRY RUN] word stats: min={min(sizes)}, max={max(sizes)}, avg={sum(sizes)//len(sizes)}")
        return {"source_key": source.key, "chunks_written": 0, "total_words": total_words, "skipped": False}

    # ── Tag and write ─────────────────────────────────────────────────────────
    from backend.ai.rag_engine import RAGEngine
    engine = RAGEngine()

    docs, metadatas, ids = [], [], []
    for idx, rc in enumerate(raw_chunks):
        condition_tags, drugs_tagged = _tag_chunk(
            rc["text"], source.condition_hints, source.drug_hints
        )
        chunk_id = _chunk_id(source.key, idx, rc["text"])
        docs.append(rc["text"])
        meta: dict = {
            "title": source.title,
            "source_key": source.key,
            "source_url": source.url,
            "source_tier": source.tier,
            "licence": source.licence,
            "chunk_index": idx,
            "condition_tags": condition_tags,
            "drugs_tagged": drugs_tagged,
        }
        if rc["page_start"] is not None:
            meta["page_start"] = rc["page_start"]
            meta["page_end"] = rc["page_end"]
        if rc["section"]:
            meta["section"] = rc["section"]
        metadatas.append(meta)
        ids.append(chunk_id)

    engine.add_documents(
        collection_name=source.collection,
        documents=docs,
        metadatas=metadatas,
        ids=ids,
    )
    print(f"  ✓ Wrote {len(raw_chunks)} chunks → collection '{source.collection}'")
    return {"source_key": source.key, "chunks_written": len(raw_chunks), "total_words": total_words, "skipped": False}


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    # Ensure stdout handles UTF-8 on Windows
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    parser = argparse.ArgumentParser(
        description="Ingest Tier-1 (and optional Tier-2) RAG sources into Concert Med Ops knowledge store."
    )
    parser.add_argument(
        "--source", metavar="KEY",
        help=f"Ingest only this source key. Available: {', '.join(ALL_SOURCES.keys())}",
    )
    parser.add_argument(
        "--local-pdf", metavar="PATH", type=Path,
        help="Use a locally-downloaded PDF instead of fetching from URL (use with --source).",
    )
    parser.add_argument(
        "--tier", type=int, choices=[1, 2], default=1,
        help="Ingest up to this tier (default: 1 = Tier-1 only, 2 = all sources).",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Fetch and chunk but do not write to the database.",
    )
    parser.add_argument(
        "--list", action="store_true",
        help="Print all source definitions and exit.",
    )
    args = parser.parse_args()

    if args.list:
        print(f"\n{'KEY':<35} {'TIER':<5} {'TYPE':<5} {'LICENCE'}")
        print("─" * 90)
        for src in TIER1_SOURCES + TIER2_SOURCES:
            print(f"{src.key:<35} {src.tier:<5} {src.source_type:<5} {src.licence[:50]}")
        return

    start = time.time()

    if args.source:
        if args.source not in ALL_SOURCES:
            print(f"Unknown source key: {args.source}")
            print(f"Available: {', '.join(ALL_SOURCES.keys())}")
            sys.exit(1)
        results = [ingest_source(ALL_SOURCES[args.source], local_pdf=args.local_pdf, dry_run=args.dry_run)]
    else:
        sources_to_run = [s for s in (TIER1_SOURCES + TIER2_SOURCES) if s.tier <= args.tier]
        results = []
        for src in sources_to_run:
            results.append(ingest_source(src, dry_run=args.dry_run))

    # Summary
    elapsed = time.time() - start
    total_chunks = sum(r["chunks_written"] for r in results)
    skipped = sum(1 for r in results if r["skipped"])

    print(f"\n{'='*60}")
    print(f"Ingestion complete in {elapsed:.1f}s")
    print(f"  Sources attempted : {len(results)}")
    print(f"  Skipped           : {skipped} (network/access failures — download manually)")
    print(f"  Chunks written    : {total_chunks}")
    if not args.dry_run and total_chunks > 0:
        from backend.ai.rag_engine import RAGEngine
        stats = RAGEngine().all_collection_stats()
        print(f"\nKnowledge store totals:")
        for col, cnt in sorted(stats.items()):
            print(f"  {col:<40} {cnt:>5} chunks")
    if skipped:
        print(
            "\nTip: For sources that failed to download (bot-blocked PDFs),\n"
            "download them manually and re-run with --local-pdf:\n"
            "  python -m backend.scripts.ingest_rag_sources \\\n"
            "    --source who_mass_gatherings \\\n"
            "    --local-pdf ~/Downloads/WHO_HSE_GCR_2015.5_eng.pdf"
        )


if __name__ == "__main__":
    main()
