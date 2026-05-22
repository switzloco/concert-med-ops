# Concert Med Ops — RAG Corpus Sources

This directory holds locally cached PDFs and extracted text used to populate the
`knowledge.sqlite` FTS5 RAG index.

Ingest all Tier-1 sources:
```bash
python -m backend.scripts.ingest_rag_sources --tier 1
```

Ingest all Tier-2 sources as well:
```bash
python -m backend.scripts.ingest_rag_sources --tier 2
```

If a PDF fails to download (bot-blocked), download it manually and re-run:
```bash
python -m backend.scripts.ingest_rag_sources \
    --source who_mass_gatherings \
    --local-pdf ~/Downloads/WHO_HSE_GCR_2015.5_eng.pdf
```

---

## Tier 1 — Must Bundle (corpus spine)

### 1. WHO Public Health for Mass Gatherings: Key Considerations (2015)
- **URL:** https://iris.who.int/bitstream/handle/10665/162109/WHO_HSE_GCR_2015.5_eng.pdf
- **Alt URL:** https://apps.who.int/iris/bitstream/handle/10665/162109/WHO_HSE_GCR_2015.5_eng.pdf
- **Licence:** CC BY-NC-SA 3.0 IGO — ingestion + QA generation permitted with attribution
- **Pages:** ~196
- **Collection:** `mass_gathering_protocols`
- **Why:** Definitive WHO operational reference for mass gathering health; direct analogue to WHO IMGS for Vessel Ops. Covers medical capacity planning, command structure, environmental health, alcohol/substance considerations, MCI preparation.
- **Script key:** `who_mass_gatherings`

### 2. SAMHSA Overdose Prevention and Response Toolkit (PEP23-03-00-001, 2024)
- **URL:** https://library.samhsa.gov/sites/default/files/overdose-prevention-response-kit-pep23-03-00-001.pdf
- **Licence:** Public Domain (US Federal Work) — no restrictions
- **Pages:** ~70
- **Collection:** `harm_reduction_protocols`
- **Why:** US federal naloxone/nalmefene reference standard. Dosing algorithms, repeat-dose intervals, xylazine considerations, post-reversal monitoring. Role-specific sections for first responders.
- **Script key:** `samhsa_overdose_toolkit`

### 3. WMS Clinical Practice Guidelines for Exercise-Associated Hyponatremia (2020)
- **URL:** https://www.wildmedcenter.com/uploads/5/9/8/2/5982510/wms_exercise-associated_hyponatremia_2020.pdf
- **Alt URL:** https://emergencymedicinecases.com/wp-content/uploads/filebase/pdf/Guidelines-EAH.pdf
- **Citation:** Bennett BL et al. *Wilderness Environ Med.* 2020;31(1):50–62. PMID: 32044213
- **Licence:** Copyrighted Elsevier/WMS; free PDFs on author mirror sites
- **Pages:** ~13
- **Collection:** `harm_reduction_protocols`
- **Why:** Gold-standard field management of exercise-associated hyponatremia, directly applicable to MDMA+water intoxication presentations. 3% NaCl bolus protocols, POC sodium thresholds.
- **Script key:** `wms_eah_2020`

### 4. ACEP Clinical Policy: Hyperactive Delirium with Severe Agitation (2021)
- **URL:** https://www.acep.org/siteassets/new-pdfs/clinical-policies/severe-agitation-cp.pdf
- **Licence:** Copyrighted ACEP; free to read
- **Pages:** ~10
- **Collection:** `harm_reduction_protocols`
- **Why:** Current US EM standard of care for agitation/sympathomimetic toxicity. Chemical sedation algorithm (ketamine, midazolam, droperidol, dose ranges). Replaces "excited delirium" language per ACMT 2023.
- **Script key:** `acep_hyperactive_delirium`

### 5. ACMT Position Statement: End the Use of the Term "Excited Delirium" (2023)
- **URL:** https://www.acmt.net/wp-content/uploads/2023/05/PS_230501_End-the-Use-of-the-Term-Excited-Delirium.pdf
- **Licence:** Copyrighted ACMT; free to read
- **Pages:** ~8
- **Collection:** `harm_reduction_protocols`
- **Why:** Updates clinical terminology and reinforces the acute management approach. Pair with ACEP policy above.
- **Script key:** `acmt_end_excited_delirium`

### 6–7. HHS CHEMM: SALT and START Triage Algorithms (Public Domain)
- **SALT URL:** https://chemm.hhs.gov/salttriage.htm
- **START URL:** https://chemm.hhs.gov/startadult.htm
- **Licence:** Public Domain (US Federal Work)
- **Collection:** `mass_gathering_protocols`
- **Why:** Official US mass-casualty triage algorithms; algorithmic format ideal for FTS5 chunking and QA generation.
- **Script keys:** `chemm_salt_triage`, `chemm_start_triage`

---

## Tier 2 — Depth Sources (run with `--tier 2`)

| Key | Source | Licence |
|---|---|---|
| `who_opioid_overdose_mgmt` | WHO Community Management of Opioid Overdose 2014 (NCBI Bookshelf) | CC BY-NC-SA 3.0 IGO |
| `emcrit_serotonin_syndrome` | EMCrit IBCC: Serotonin Syndrome | Copyrighted, free-to-read |
| `emcrit_sympathomimetic` | EMCrit IBCC: Sympathomimetic Toxicity | Copyrighted, free-to-read |
| `emcrit_opioid_intoxication` | EMCrit IBCC: Opioid Intoxication | Copyrighted, free-to-read |
| `emcrit_ghb` | EMCrit IBCC: GHB/GBL | Copyrighted, free-to-read |
| `emcrit_rhabdomyolysis` | EMCrit IBCC: Rhabdomyolysis | Copyrighted, free-to-read |
| `emcrit_hyperthermia` | EMCrit IBCC: Hyperthermia / Heat Stroke | Copyrighted, free-to-read |
| `emcrit_hyponatremia` | EMCrit IBCC: Hyponatremia | Copyrighted, free-to-read |

EMCrit note: Ingest for internal RAG use; surface answers with citations; do not redistribute raw chapter text in the product binary.

---

## Licensing summary

| Source | Licence | Redistribute raw text? | Derive QA pairs? |
|---|---|---|---|
| WHO Mass Gatherings 2015 | CC BY-NC-SA 3.0 IGO | ✅ With attribution | ✅ |
| SAMHSA Toolkits / TIPs | Public Domain (US Federal) | ✅ No restrictions | ✅ |
| CHEMM triage pages | Public Domain (US Federal) | ✅ No restrictions | ✅ |
| WMS EAH Guidelines | Copyrighted (Elsevier) | ❌ Internal only | ⚠️ Internal research use |
| ACEP Clinical Policy | Copyrighted (ACEP) | ❌ Internal only | ⚠️ Internal research use |
| ACMT Position Statement | Copyrighted (ACMT) | ❌ Internal only | ⚠️ Internal research use |
| EMCrit IBCC chapters | Copyrighted (EMCrit) | ❌ Internal only | ⚠️ Internal research use |

**Safe shipping strategy:** bundle only the SQLite FTS5 index (embeddings/BM25 tokens), not
the source PDFs. The product retrieves short excerpts at query-time. This is consistent with
fair-use citation practices. For commercial distribution, get explicit permission from
ACEP/EMCrit/Elsevier or limit bundled text to the public-domain sources only.

---

## Adding new sources

1. Add a `Source(...)` entry to `TIER2_SOURCES` in `backend/scripts/ingest_rag_sources.py`.
2. Add relevant `condition_hints` and `drug_hints` to ensure good tagging.
3. Run: `python -m backend.scripts.ingest_rag_sources --source your_new_key`
