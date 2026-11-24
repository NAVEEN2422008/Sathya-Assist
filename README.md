# Sathya Assist 🤖🎓

> **An AI Campus Companion for Sathyabama Students**  
> Built with ❤️ by the **Microsoft Club (AI/ML Subgroup)** at **Sathyabama Institute of Science and Technology**.

---

## 📌 Project Overview
Students often spend hours sifting through WhatsApp forwards, outdated notice boards, and scattered university circulars to find basic answers about exams, hostel rules, academic schedules, and placement requirements.

**Sathya Assist** is an AI chatbot powered by Retrieval-Augmented Generation (RAG). It provides accurate, source-grounded answers to student queries directly from official campus circulars, handbooks, and verified community FAQs.

---

## 🏛️ Repository Organization

```text
├── docs/                          # Project specifications & architecture briefs
│   ├── DATA_ARCHITECTURE.md       # Data engineering standards & RAG spec
│   └── Sathya Assist – AI_ML Project Brief.pdf
├── src/                           # Reusable core Python package
│   └── sathya_assist/             # Config, extractors, cleanings, and chunkers
├── scripts/                       # Executable CLI workflows
│   ├── clean_and_chunk.py         # Automated extraction, date normalization & chunking
│   ├── download_official_docs.py  # Navigation downloader for genuine PDFs & HTML
│   └── scrape_and_clean.py        # Web scraping, table extraction & manifest logging
└── data/
    ├── raw/                       # Immutable authentic official files (PDF & HTML)
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

## 🔒 Privacy & Compliance (Zero-PII & Zero-Hallucination)
Sathya Assist strictly adheres to university privacy and factual accuracy:
- **Zero-Hallucination Directive**: Every fact, rule, and schedule is backed by a verifiable URL and SHA-256 hash in `data/metadata/data_manifest.json`.
- **Zero-PII Policy**: Automated PII scrubbing masks student register numbers, personal email addresses, and phone numbers before documents reach the vector database.

---

## 🚀 Quick Start & Usage

### 1. Installation
Install project dependencies:
```bash
pip install -r requirements.txt
```

### 2. Ingesting & Verifying Official Documents
To fetch and update the official circulars and regulations:
```bash
python scripts/download_official_docs.py
```

### 3. Cleaning & Generating Vector Chunks
To clean text, normalize dates, redact PII, and generate chunks with metadata:
```bash
python scripts/clean_and_chunk.py
```

Outputs will be populated in:
- `data/processed/<category>/`: Cleaned Markdown files.
- `data/chunks/`: Semantic JSON chunks ready for vector embeddings.
- `data/metadata/doc_catalog.csv`: Updated document catalog.

---

## 🤝 Contributing FAQs
To add common student questions:
1. Update [data/processed/verified_faqs.json](file:///c:/Users/Naveen%20S/Documents/mc%20ml/data/processed/verified_faqs.json) ensuring every answer includes an exact `verbatim_excerpt` and `source_document` reference.

---

## 👥 Team
- **AI/ML Subgroup**: Data Engineering, RAG Pipeline, Prompt Engineering, Evaluation.
- **Web & App Development**: Official chat widget and platform integration.
- **Cloud & DevOps**: Azure deployment and vector database management.
- **Microsoft Club, Sathyabama Institute of Science and Technology**.
