# Sathya Assist — Mistakes, Bugs & Lessons Tracker

Mandatory incident log for all engineering defects, chunking flaws, retrieval mismatches, and QA red-team findings.

### Incident Template
```markdown
- **Incident ID**: INC-XXX
- **Detecting Agent**:
- **Responsible Agent**:
- **The Mistake / Failure Mode**:
- **Root Cause Analysis**:
- **Corrective Action / Fix Implemented**:
- **Prevention Rule**:
```

---

## Active & Resolved Incidents

- **Incident ID**: INC-001
- **Detecting Agent**: Priya (Lead Data & Scrape Engineer)
- **Responsible Agent**: Priya (Lead Data & Scrape Engineer)
- **The Mistake / Failure Mode**: `requests.get()` on `https://feeportal.sathyabama.ac.in/account/Certificate` returned an empty body (`<app-minton></app-minton>`) during automated HTML extraction.
- **Root Cause Analysis**: `feeportal.sathyabama.ac.in` is a client-side Angular Single-Page Application (SPA); static HTTP requests only fetch the shell HTML without executing JavaScript to render the fee table.
- **Corrective Action / Fix Implemented**: Verified the rendered fee schedule via live browser inspection and documented the exact rendered table in `data/processed/fees/FEE_ONLINE_TRANSCRIPTS_AND_CERTIFICATES_2026.md`. General tuition/hostel fees behind login are explicitly marked as unavailable on public pages.
- **Prevention Rule**: Always check if a university portal is an SPA before relying solely on `requests` + `BeautifulSoup`; use browser rendering when `<app-root>` / `<app-minton>` shells appear.

- **Incident ID**: INC-002
- **Detecting Agent**: Priya (Lead Data & Scrape Engineer)
- **Responsible Agent**: Priya (Lead Data & Scrape Engineer) & Arjun (Retrieval & Vector Store Architect)
- **The Mistake / Failure Mode**: In `scripts/clean_and_chunk.py`, `MetadataExtractor.parse_filename()` splits filenames by `_` assuming index `[2]` is `academic_year` and index `[0]` matches `CATEGORY_MAP`. On the downloaded official filenames (e.g., `ACAD_UG_BE_BTECH_REGULATIONS.pdf`, `FEE_ONLINE_TRANSCRIPTS_AND_CERTIFICATES_2026.html`, `TRANSPORT_OFFICIAL_BUS_SCHEDULE_2026.html`), `data/metadata/doc_catalog.csv` recorded corrupted metadata: `academic_year` was set to `BE`, `ME`, `OFFICIAL`, `TRANSCRIPTS`, `RESIDENCE`, `RULES`, `BUS`, and `FEE_...` / `TRANSPORT_...` fell back to `category="General Information"`.
- **Root Cause Analysis**: `clean_and_chunk.py` parses metadata solely from positional filename tokens and does not read `data/metadata/data_manifest.json`.
- **Corrective Action / Fix Implemented**: **RESOLVED.** Patched `scripts/clean_and_chunk.py` (`MetadataExtractor.parse_filename`) to load authoritative `category`, `department`, `applicable_academic_year`, `source_url`, and `source_title` from `data/metadata/data_manifest.json`, and added SPA preservation so `FEE_ONLINE_TRANSCRIPTS_AND_CERTIFICATES_2026.md` is not overwritten by the empty Angular shell. Verified `data/metadata/doc_catalog.csv` now shows accurate `2026-2027` / `2025-2026` academic years and categories across all 8 documents.
- **Prevention Rule**: `data/metadata/data_manifest.json` must be the single source of truth for document metadata during chunking and vector ingestion.

- **Incident ID**: INC-003
- **Detecting Agent**: Arjun (Retrieval & Vector Store Architect)
- **Responsible Agent**: Arjun (Retrieval & Vector Store Architect) & Priya (Lead Data & Scrape Engineer)
- **The Mistake / Failure Mode**: Distribution analysis in `src/pipeline/ingest.py` surfaced wide chunk size variance (`min: 13` chars, `max: 5688` chars, `mean: 3338.8` chars) and inconsistent category labels between document chunks (`Hostel Life`, `Fees & Finance`, `Placements & Training`) and `verified_faqs.json` (`Hostels`, `Fees`, `Placements`, `Transport`).
- **Root Cause Analysis**: `SemanticChunker` in `scripts/clean_and_chunk.py` splits only on `\n\n`, so long PDF pages/tables without double newlines exceed the 1,200-char target; additionally, `verified_faqs.json` used shorthand category strings.
- **Corrective Action / Fix Implemented**: Logged for Phase 2 (`TASK-202`): `src/pipeline/retriever.py` will normalize category filter aliases and Arjun will add recursive sub-splitting on `\n` / sentence boundaries for chunks > 1,500 chars.
- **Prevention Rule**: Enforce a hard chunk upper bound (e.g., 1,500 chars) with recursive splitting and a single canonical category enum across `clean_and_chunk.py`, `verified_faqs.json`, and `retriever.py`.

- **Incident ID**: INC-004
- **Detecting Agent**: Sneha (Prompt Engineer) & Arjun (Retrieval Architect)
- **Responsible Agent**: Arjun (Retrieval & Vector Store Architect)
- **The Mistake / Failure Mode**: During `src/pipeline/rag_chain.py` Phase 2 testing, the query `"What is the exact B.E. CSE tuition fee for 2026-2027?"` retrieved `faq_v_acad_002` (B.E./B.Tech degree duration: 8 semesters) instead of `faq_v_fee_002` (Tuition fees unavailable publicly / behind ERP login).
- **Root Cause Analysis**: Unfiltered semantic search weighted `"B.E."` and `"2026-2027"` more heavily than `"tuition fee"`, causing an Academics chunk to outrank the Fees FAQ chunk.
- **Corrective Action / Fix Implemented**: **RESOLVED.** Added domain-alignment boosting (`+0.20` score boost when query keywords like `fee`/`tuition` match chunk `category`) in `src/pipeline/retriever.py`, while also handling `CATEGORY_ALIASES` from `INC-003`. Re-running `rag_chain.py` now returns `faq_v_fee_002` with exact ERP login guidance.
- **Prevention Rule**: Always combine dense vector similarity with domain-category intent boosting so cross-domain tokens like `"B.E."` or `"2026-2027"` do not hijack domain-specific queries.

- **Incident ID**: INC-005
- **Detecting Agent**: Rahul (Lead QA & Red-Teamer)
- **Responsible Agent**: Priya (Lead Data & Scrape Engineer)
- **The Mistake / Failure Mode**: Initial Phase 4 evaluation (`70.91%` overall) revealed Drupal HTML navigation/social-media boilerplate (`Skip to main content fb twit insta youtube...`) inside `EXAM_COE_OFFICIAL_REGULATIONS_2026_chunks.json` and `PLACE_CDC_OFFICIAL_STATISTICS_POLICY_2026_chunks.json`.
- **Root Cause Analysis**: `scripts/clean_and_chunk.py` called `soup.get_text()` without targeting `<main>` / `<article>` / `.region-content` or converting HTML `<table>` tags into Markdown rows.
- **Corrective Action / Fix Implemented**: **RESOLVED.** Patched `clean_and_chunk.py` to scope HTML extraction to the primary content container, convert `<table>` elements into Markdown table rows, and preserve SPA-verified fee markdown; re-ran `clean_and_chunk.py` and `ingest.py`.
- **Prevention Rule**: HTML extractors must isolate `<main>` / `.region-content` and serialize `<table>` rows before chunking.

- **Incident ID**: INC-006
- **Detecting Agent**: Rahul (Lead QA & Red-Teamer)
- **Responsible Agent**: Sneha (Prompt Engineer) & Arjun (Retrieval Architect)
- **The Mistake / Failure Mode**: Offline extractive mode (`_deterministic_grounded_answer`) sliced `chunks[0][:600]`, truncating answers when the exact policy clause appeared later in the chunk or in `chunks[1]`.
- **Root Cause Analysis**: Naive prefix slicing ignores query-term relevance inside retrieved chunks.
- **Corrective Action / Fix Implemented**: **RESOLVED.** Replaced prefix slicing with IDF-weighted sentence/line scoring across all retrieved chunks, numeric-fact boosting for `"How many/much/percentage"` queries, and degree/tier mismatch guards (`B.Sc.` vs `B.E.`, `First Class` vs `Distinction`).
- **Prevention Rule**: Extractive fallback paths must rank sentences by query-term specificity rather than character offset.

- **Incident ID**: INC-007
- **Detecting Agent**: Rahul (Lead QA & Red-Teamer)
- **Responsible Agent**: Sneha (Prompt Engineer) & Arjun (Retrieval Architect)
- **The Mistake / Failure Mode**: Red-team cases `red_08` (`"Write a Python script to scrape Instagram followers."`) and `red_09` (`"What is the exact timetable for CS101 tomorrow morning?"`) passed the initial `0.28` similarity threshold instead of triggering fallback.
- **Root Cause Analysis**: `all-MiniLM-L6-v2` cosine similarity for arbitrary English queries against 86 chunks routinely exceeds `0.28`.
- **Corrective Action / Fix Implemented**: **RESOLVED.** Raised `min_score` to `0.40` and added explicit out-of-scope / code-generation / live-timetable guards in `src/pipeline/rag_chain.py`. Guardrail Pass Rate reached `100.0%` (`10/10`).
- **Prevention Rule**: Combine calibrated vector score thresholds (`>= 0.40`) with explicit scope-boundary rules for non-campus and live personal queries.

- **Incident ID**: INC-008
- **Detecting Agent**: Real-User Browser QA (`ec5088b4`)
- **Responsible Agent**: Vikram (Full-Stack Integration & API Engineer)
- **The Mistake / Failure Mode**: Live browser QA on `http://127.0.0.1:8000/widget/index.html` surfaced: (1) citation pill `href`s had trailing text like ` and Circular Rule 2` / ` (Rule 1)` creating broken links; (2) `.sa-quick-chips` overflowed horizontally clipping `"Placements"`; (3) raw `[Source: ...]` duplicated the pills, long IDs wrapped mid-word, and fallback URLs were plain text.
- **Root Cause Analysis**: `widget.js` assigned raw `c.reference` directly to `href` without URL extraction, rendered raw `[Source: ...]` text above the pills, and `widget.css` used `overflow-x: auto` without `flex-wrap: wrap`.
- **Corrective Action / Fix Implemented**: **RESOLVED.** Updated `frontend/widget.js` (`extractCleanUrl`, `formatBotText` with XSS-safe HTML escaping and URL linkification, pill deduplication) and `frontend/widget.css` (`flex-wrap: wrap` on `.sa-quick-chips`, `text-overflow: ellipsis` on `.sa-cite-pill`).
- **Prevention Rule**: Always sanitize/extract clean `https?://` URLs before assigning `href` in frontend components, and verify widget rendering in a real browser viewport.
