# Sathya Assist - Data Engineering Architecture

## 1. Overview
This repository contains the primary document knowledge base, data cleaning engines, and chunking pipeline for **Sathya Assist**, the RAG AI chatbot for Sathyabama students developed by the Microsoft Club.

---

## 2. Directory Hierarchy

```text
├── .gitignore                     # Git ignore patterns
├── README.md                      # Primary project overview & quickstart
├── requirements.txt               # Python package dependencies
├── docs/                          # Project specifications & architecture briefs
│   ├── DATA_ARCHITECTURE.md       # Data engineering standards & RAG spec
│   └── Sathya Assist – AI_ML Project Brief.pdf
├── config/                        # Shared configurations & category mappings
├── src/                           # Core reusable Python package
│   └── sathya_assist/
│       ├── __init__.py
│       └── config.py
├── scripts/                       # Executable CLI workflows
│   ├── __init__.py
│   ├── clean_and_chunk.py         # Automated extraction, date normalization & chunking
│   ├── download_official_docs.py  # Navigation downloader for genuine PDFs & HTML
│   └── scrape_and_clean.py        # Web scraping, table extraction & manifest logging
└── data/
    ├── raw/                       # Immutable authentic official files
    │   ├── academics/             # UG/PG Regulations PDFs
    │   ├── exams/                 # COE official examination web portals
    │   ├── hostels/               # Hostel rules circular PDF, mess & bus routes
    │   ├── placements/            # CDC recruitment statistics & upgrade policies
    │   └── fees/                  # Official transcript fee schedules
    ├── processed/                 # Cleaned Markdown & FAQ documents by category
    │   ├── academics/
    │   ├── exams/
    │   ├── hostels/
    │   ├── placements/
    │   ├── fees/
    │   └── verified_faqs.json     # 16 authentic Q&As mapped to verbatim quotes
    ├── chunks/                    # Vector-ready chunks with rich metadata
    └── metadata/                  # Provenance tracking & audit
        ├── data_manifest.json     # SHA-256 hashes & access timestamps
        ├── doc_catalog.csv        # Master document catalog
        └── pii_audit_log.jsonl    # Zero-PII compliance audit log
```

---

## 3. Provenance & Data Verification
- **Source Policy**: Only public circulars and official webpages from `sathyabama.ac.in` and `feeportal.sathyabama.ac.in` are ingested.
- **Verification**: Every document has an entry in `data/metadata/data_manifest.json` with its SHA-256 hash, official contact department, and source URL.
- **Privacy**: All student register numbers, personal emails, and phone numbers are redacted before indexing.
