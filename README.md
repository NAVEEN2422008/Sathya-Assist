# Sathya Assist

Campus Q&A assistant for Sathyabama Institute of Science and Technology students, built by the Microsoft Club (AI/ML Subgroup).

## Overview

**Sathya Assist** uses Retrieval-Augmented Generation (RAG) to answer student questions about exams, hostel rules, academic regulations, transport, and placements using official university circulars and verified FAQs.

## Repository Structure

```text
├── docs/                          # Project brief and data architecture docs
│   ├── DATA_ARCHITECTURE.md
│   └── Sathya Assist – AI_ML Project Brief.pdf
├── src/
│   └── sathya_assist/             # Shared configuration and constants
├── scripts/                       # Data ingestion, cleaning, and chunking scripts
│   ├── clean_and_chunk.py         # Text extraction, date normalization, PII redaction, chunking
│   ├── download_official_docs.py  # Batch downloader for official PDFs and pages
│   └── scrape_and_clean.py        # HTML/PDF parser and manifest updater
└── data/
    ├── raw/                       # Source PDFs and HTML snapshots by category
    │   ├── academics/
    │   ├── exams/
    │   ├── hostels/
    │   ├── placements/
    │   └── fees/
    ├── processed/                 # Cleaned Markdown files and verified FAQs
    │   ├── academics/
    │   ├── exams/
    │   ├── hostels/
    │   ├── placements/
    │   ├── fees/
    │   └── verified_faqs.json
    ├── chunks/                    # Chunked JSON files with metadata for vector indexing
    └── metadata/                  # Provenance and catalog files
        ├── data_manifest.json
        └── doc_catalog.csv
```

## Data Privacy & Source Verification

- **Official Sources Only**: Documents are sourced from public pages and circulars on `sathyabama.ac.in` and `feeportal.sathyabama.ac.in`, tracked with SHA-256 checksums in `data/metadata/data_manifest.json`.
- **No Student PII**: The cleaning pipeline redacts student register numbers, personal email addresses, and phone numbers before chunking.

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Fetch Official Documents
```bash
python scripts/download_official_docs.py
```

### 3. Clean & Chunk Documents
```bash
python scripts/clean_and_chunk.py
```

This generates:
- `data/processed/<category>/`: Cleaned Markdown files.
- `data/chunks/`: Semantic JSON chunks with metadata.
- `data/metadata/doc_catalog.csv`: Updated document catalog.

## Contributing FAQs

Add entries to `data/processed/verified_faqs.json` with a `verbatim_excerpt` and `source_document` reference from an official circular or university page.

## Team

- **AI/ML Subgroup**: Data Engineering, RAG Pipeline, Prompt Engineering, Evaluation
- **Web & App Development**: Chat widget and platform integration
- **Cloud & DevOps**: Azure deployment and vector store hosting
