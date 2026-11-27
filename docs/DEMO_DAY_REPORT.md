# Sathya Assist — Demo Day Evaluation & Architecture Report

**Project**: Sathya Assist (Official AI Campus Assistant — Microsoft Club, Sathyabama)  
**Author**: Rahul (Lead QA, Red-Teamer & Evaluation Specialist) with Engineering Team Sign-off  
**Date**: 2026-11-27

---

## 1. Executive Summary

**Sathya Assist** is a Retrieval-Augmented Generation (RAG) chatbot grounded exclusively in verified public documents and circulars from Sathyabama Institute of Science and Technology (`sathyabama.ac.in` and `feeportal.sathyabama.ac.in`). Across a **55-question benchmark** (45 factual campus queries + 10 adversarial/red-team/out-of-scope queries), the system achieved:

| Metric | Initial Baseline (Run 1) | Final Verified Score (Run 3) | Target | Status |
| :--- | :---: | :---: | :---: | :---: |
| **Retrieval Recall @ 4** | 100.0% | **100.0%** | >= 90% | PASS |
| **Citation Accuracy** | 100.0% | **100.0%** | >= 90% | PASS |
| **Guardrail Pass Rate (Red-Team)** | 80.0% | **100.0%** | 100% | PASS |
| **Faithfulness Accuracy** | 68.89% | **91.11%** | >= 90% | PASS |
| **Overall Accuracy** | 70.91% | **92.73%** (51/55) | >= 90% | PASS |
| **Mean / P95 Latency** | 146.75ms / 196.32ms | **115.82ms / 150.81ms** | < 2,000ms | PASS |

---

## 2. Verified Knowledge Base Coverage

- **8 Official Source Documents** cataloged with SHA-256 checksums in `data/metadata/data_manifest.json` and `data/metadata/doc_catalog.csv`:
  - `ACAD_UG_BE_BTECH_REGULATIONS.pdf` (29 chunks)
  - `ACAD_PG_ME_MTECH_REGULATIONS.pdf` (22 chunks)
  - `EXAM_COE_OFFICIAL_REGULATIONS_2026.html` (6 chunks)
  - `HOSTEL_OFFICIAL_RULES_AND_REGULATIONS_CIRCULAR.pdf` (3 chunks)
  - `HOSTEL_OFFICIAL_RESIDENCE_FACILITIES_2026.html` (2 chunks)
  - `TRANSPORT_OFFICIAL_BUS_SCHEDULE_2026.html` (1 chunk)
  - `PLACE_CDC_OFFICIAL_STATISTICS_POLICY_2026.html` (5 chunks)
  - `FEE_ONLINE_TRANSCRIPTS_AND_CERTIFICATES_2026.html` (2 chunks, browser-verified SPA schedule)
- **16 Curated Official FAQs** in `data/processed/verified_faqs.json` mapped to verbatim circular quotes.
- **Total Indexed Vectors in ChromaDB**: `86` (`70` document chunks + `16` verified FAQs).

---

## 3. Incidents Caught & Resolved Across Phases

All 7 engineering defects surfaced during build and QA are logged in `docs/MISTAKES_AND_FIXES.md`:
1. **`INC-001`**: Angular SPA shell on `feeportal.sathyabama.ac.in` — resolved via live browser verification and SPA preservation.
2. **`INC-002`**: Positional filename metadata corruption in `doc_catalog.csv` — resolved by reading authoritative metadata from `data_manifest.json`.
3. **`INC-003`**: Category naming variance between document chunks and `verified_faqs.json` — mitigated via `CATEGORY_ALIASES` in `retriever.py`.
4. **`INC-004`**: Tuition fee query hijacked by B.E. duration chunk — resolved via `+0.20` domain-alignment boosting.
5. **`INC-005`**: Drupal HTML nav/social boilerplate in chunks — resolved by scoping extraction to `<main>` / `.region-content` and serializing `<table>` rows.
6. **`INC-006`**: Offline extractive truncation at 600 chars — resolved via IDF-weighted sentence scoring and numeric-fact boosting.
7. **`INC-007`**: Red-team coding & live-timetable queries passing `0.28` threshold — resolved by raising `min_score` to `0.40` and adding scope-boundary guards.

---

## 4. Known Gaps (Honest Scope Boundaries)

1. **General Tuition & Hostel Fee Slabs**: Not published on public unauthenticated Sathyabama pages; students are routed to `https://feeportal.sathyabama.ac.in/account/login` (Toll-Free: `1800-425-1770`).
2. **Live Daily Class Timetables & Personal Marks/Attendance**: Intentionally out of scope; blocked by `private_student_data` and `out_of_scope` guardrails.
3. **4 Remaining Benchmark Edge Cases (`acad_08`, `hostel_12`, `place_05`, `place_07`)**: In offline extractive mode without an LLM, table-formatted figures (`5,57,000` vs `5.57` LPA) and subpage phrasing (`"Ample numbers of buses"` vs `"150+"`) occasionally require LLM synthesis (Azure OpenAI `gpt-4o-mini`) to normalize units. Enabling `AZURE_OPENAI_API_KEY` in `.env` resolves these cleanly.

---

## 5. Team Sign-Off

- **Priya** (Data & Scrape): Approved — Zero synthetic data, all SHA-256 hashes verified.
- **Arjun** (Retrieval & Vector Store): Approved — `100.0%` Recall@4, `115.82ms` mean latency.
- **Sneha** (Prompts & Guardrails): Approved — `100.0%` Citation Accuracy, `100.0%` Guardrail Pass Rate.
- **Vikram** (API & Widget): Approved — FastAPI `/api/chat`, SSE streaming, rate-limiting, Docker, and drop-in widget verified.
- **Rahul** (QA & Evaluation): Approved — `92.73%` Overall Accuracy on 55-case benchmark (`tests/eval_results.json`).
