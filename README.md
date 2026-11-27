# Sathya Assist

Campus Q&A assistant for Sathyabama Institute of Science and Technology students, built by the Microsoft Club (AI/ML Subgroup).

## Overview

**Sathya Assist** uses Retrieval-Augmented Generation (RAG) to answer student questions about exams, hostel rules, academic regulations, transport, fees, and placements using official university circulars and verified FAQs. Every answer includes verifiable source citations, and out-of-scope or private student queries route directly to the appropriate university office.

## Repository Structure

```text
├── docs/                          # Project brief, architecture, task board, and Demo Day report
│   ├── DATA_ARCHITECTURE.md
│   ├── DEMO_DAY_REPORT.md
│   ├── TASK_BOARD.md
│   ├── COLLABORATION_LOG.md
│   ├── MISTAKES_AND_FIXES.md
│   └── Sathya Assist – AI_ML Project Brief.pdf
├── src/
│   ├── api/
│   │   └── main.py                # FastAPI backend (/api/chat, /api/health, /api/feedback, /widget)
│   ├── pipeline/
│   │   ├── ingest.py              # ChromaDB ingestion & chunk distribution analysis
│   │   ├── retriever.py           # Hybrid semantic + keyword + domain-aligned retriever
│   │   └── rag_chain.py           # End-to-end RAG chain with guardrails & citation formatting
│   ├── prompts/
│   │   └── system_prompt.py       # Production system prompt & official office fallback routing
│   └── sathya_assist/             # Shared configuration constants
├── frontend/                      # Plug-and-play embeddable chat widget (HTML/CSS/JS)
│   ├── index.html
│   ├── widget.js
│   └── widget.css
├── scripts/                       # Data ingestion, cleaning, and chunking CLI scripts
│   ├── clean_and_chunk.py
│   ├── download_official_docs.py
│   └── scrape_and_clean.py
├── tests/                         # 55-question evaluation benchmark & red-team suite
│   ├── evaluation_benchmark.json
│   ├── run_eval.py
│   └── eval_results.json
├── data/
│   ├── raw/                       # Source PDFs and HTML snapshots by category
│   ├── processed/                 # Cleaned Markdown files and verified_faqs.json
│   ├── chunks/                    # Chunked JSON files with metadata for vector indexing
│   └── metadata/                  # data_manifest.json & doc_catalog.csv
├── Dockerfile
├── .env.example
└── requirements.txt
```

## Evaluation Results (55-Case Benchmark)

Tested via `python tests/run_eval.py` (see [docs/DEMO_DAY_REPORT.md](docs/DEMO_DAY_REPORT.md)):

- **Retrieval Recall@4**: `100.0%`
- **Citation Accuracy**: `100.0%`
- **Guardrail Pass Rate (PII / Prompt Injection / Out-of-Scope)**: `100.0%`
- **Faithfulness Accuracy**: `91.11%`
- **Overall Accuracy**: `92.73%` (`51/55`)
- **Latency (Mean / P95)**: `115.82ms / 150.81ms`

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
cp .env.example .env
```

### 2. Build Knowledge Base & Vector Store
```bash
python scripts/clean_and_chunk.py
python src/pipeline/ingest.py
```

### 3. Run the FastAPI Server & Chat Widget
```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```
Open `http://localhost:8000/widget/index.html` to test the embeddable chat widget, or `http://localhost:8000/docs` for Swagger API docs.

### 4. Run Evaluation Suite
```bash
python tests/run_eval.py
```

### 5. Docker Deployment
```bash
docker build -t sathya-assist .
docker run -p 8000:8000 --env-file .env sathya-assist
```

## Team
- **Priya** — Lead Data & Scrape Engineer
- **Arjun** — Retrieval & Vector Store Architect
- **Sneha** — Prompt Engineer & Safety Guardrail Architect
- **Vikram** — Full-Stack Integration & API Engineer
- **Rahul** — Lead QA, Red-Teamer & Evaluation Specialist
