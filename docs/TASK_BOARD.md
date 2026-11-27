# Sathya Assist — Engineering Task Board

Live Kanban tracker for the 5-agent engineering team.
Statuses: `[Backlog]` → `[In Progress]` → `[In Review]` → `[Done]` → `[Blocked]`

---

## [Done]
- **TASK-001: Sprint 0 Workspace & Coordination Infrastructure**
  - **Assigned Agent**: Swarm Coordinator (Engineering Director)
  - **Priority**: P0 (Critical)
  - **Acceptance Criteria**: `src/`, `data/`, `tests/`, `docs/`, `frontend/` directories initialized; `docs/TASK_BOARD.md`, `docs/COLLABORATION_LOG.md`, and `docs/MISTAKES_AND_FIXES.md` created.
  - **Dependency**: None

- **TASK-101: Phase 1 — Official Data Audit & Pipeline Verification**
  - **Assigned Agent**: Priya (Lead Data & Scrape Engineer)
  - **Priority**: P0 (Critical)
  - **Acceptance Criteria**: Verified all 8 documents in `data/metadata/data_manifest.json` have valid `sathyabama.ac.in` / `feeportal.sathyabama.ac.in` URLs, SHA-256 hashes, timestamps, and zero synthetic/mock content; patched `INC-002` in `scripts/clean_and_chunk.py` so manifest metadata and SPA-verified fee markdown are preserved; regenerated 82 chunks and `data/metadata/doc_catalog.csv`.
  - **Dependency**: TASK-001

- **TASK-102: Phase 1 — Chunking Analysis & ChromaDB Ingestion Pipeline (`src/pipeline/ingest.py`)**
  - **Assigned Agent**: Arjun (Retrieval & Vector Store Architect)
  - **Priority**: P0 (Critical)
  - **Acceptance Criteria**: Inspected Priya's cleaned Markdown files and chunks; built `src/pipeline/ingest.py` to analyze text distributions and persist 98 vectors (82 document chunks + 16 verified FAQs) into `data/chroma_db` (`sathya_assist_kb`) with full metadata preservation and verified smoke-test retrieval.
  - **Dependency**: TASK-101

- **TASK-201: Phase 2 — System Prompt & Citation Guardrails (`src/prompts/system_prompt.py`)**
  - **Assigned Agent**: Sneha (Prompt Engineer & Safety Guardrail Architect)
  - **Priority**: P0 (Critical)
  - **Acceptance Criteria**: Implemented `SYSTEM_PROMPT` with `[Source: <document_id> | <section_or_url>]` citation format, few-shot examples, prompt-injection defense, and `get_fallback_response()` routing to COE/Warden/Transport/CDC/Fee Portal.
  - **Dependency**: TASK-102

- **TASK-202: Phase 2 — Hybrid Retriever (`src/pipeline/retriever.py`) & RAG Chain (`src/pipeline/rag_chain.py`)**
  - **Assigned Agent**: Arjun & Sneha
  - **Priority**: P0 (Critical)
  - **Acceptance Criteria**: Built `SathyaRetriever` with `CATEGORY_ALIASES` (`INC-003`), lexical boosting, and domain-alignment boost (`INC-004`); wired into `SathyaRAGChain` and verified 7/7 test queries (including PII block, prompt-injection block, and out-of-scope fallback) at <500ms latency.
  - **Dependency**: TASK-102, TASK-201

- **TASK-301: Phase 3 — FastAPI Backend (`src/api/main.py`)**
  - **Assigned Agent**: Vikram (Full-Stack Integration & API Engineer)
  - **Priority**: P1 (High)
  - **Acceptance Criteria**: Implemented `/api/chat` (JSON + SSE streaming), `/api/health`, `/api/feedback`, CORS, sliding-window IP rate limiter (30 RPM), `.env.example`, `Dockerfile`, and `requirements.txt`. Verified all endpoints via `TestClient` (`286.25ms` chat latency, `98` vectors indexed).
  - **Dependency**: TASK-202

- **TASK-302: Phase 3 — Embeddable Chat Widget (`frontend/widget.js`, `frontend/widget.css`)**
  - **Assigned Agent**: Vikram (Full-Stack Integration & API Engineer)
  - **Priority**: P1 (High)
  - **Acceptance Criteria**: Built drop-in HTML/CSS/JS chat widget (`frontend/widget.js`, `frontend/widget.css`, `frontend/index.html`) with quick-reply chips, clickable citation pills, and `/api/feedback` integration, mounted at `/widget`.
  - **Dependency**: TASK-301

- **TASK-401: Phase 4 — Evaluation Benchmark & Red-Teaming (`tests/evaluation_benchmark.json`, `tests/run_eval.py`)**
  - **Assigned Agent**: Rahul (Lead QA, Red-Teamer & Evaluation Specialist)
  - **Priority**: P0 (Critical)
  - **Acceptance Criteria**: Designed 55-question benchmark (45 factual + 10 red-team/PII/injection/out-of-scope); resolved `INC-005`, `INC-006`, and `INC-007` with Priya/Sneha/Arjun; achieved `100.0%` Recall@4, `100.0%` Citation Accuracy, `100.0%` Guardrail Pass Rate, `91.11%` Faithfulness, and `92.73%` Overall Accuracy at `115.82ms` mean latency.
  - **Dependency**: TASK-202, TASK-301

- **TASK-402: Phase 4 — Demo Day Report (`docs/DEMO_DAY_REPORT.md`) & Final `README.md`**
  - **Assigned Agent**: Rahul (with Team Sign-off)
  - **Priority**: P1 (High)
  - **Acceptance Criteria**: Empirical evaluation metrics, incident resolution summary, known gaps, and complete setup/Docker documentation published.
  - **Dependency**: TASK-401

---

## [In Progress]
*(All Phases 1–4 Complete)*

---

## [Backlog]
*(Empty — Ready for Demo Day)*

---

## [In Review]
*(None)*

---

## [Blocked]
*(None)*
