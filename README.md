# Sathya Assist 🤖🎓

> **An AI Campus Companion for Sathyabama Students**  
> Built with ❤️ by the **Microsoft Club (AI/ML Subgroup)** at **Sathyabama Institute of Science and Technology**.

---

## 📌 Project Overview
Students often spend hours sifting through WhatsApp forwards, outdated notice boards, and scattered university circulars to find basic answers about exams, hostel rules, academic schedules, and placement requirements.

**Sathya Assist** is an AI chatbot powered by Retrieval-Augmented Generation (RAG). It provides accurate, source-grounded answers to student queries directly from official campus circulars, handbooks, and verified community FAQs.

---

## 🏛️ Knowledge Base Architecture

```text
data/
├── raw/                      # Immutable, pristine source documents
│   ├── academics/            # Academic calendars, working hours, attendance policies
│   ├── examinations/         # COE regulations, grading scales, arrear rules, revaluation
│   ├── hostels/              # Gate timings, curfew, dining mess, laundry, campus hospital
│   ├── finance_fees/         # Tuition deadlines, transport and exam fee schedules
│   ├── placements/           # CDC criteria, Dream/Super Dream upgrade thresholds
│   ├── club_events/          # Microsoft Club symposiums, hackathons, workshops
│   └── faqs_community/       # Crowdsourced WhatsApp queries & senior verified Q&As (JSON)
│
├── processed/
│   ├── text/                 # Cleaned Markdown docs (headers/footers stripped, dates normalized)
│   └── chunks/               # Chunked JSON vectors enriched with granular metadata
│
└── metadata/
    ├── doc_catalog.csv       # Master provenance registry (file hashes, chunk counts, departments)
    └── pii_audit_log.jsonl   # Audit log capturing masked student roll numbers / phone numbers
```

---

## 🔒 Privacy & Compliance (Zero-PII Policy)
Sathya Assist strictly adheres to student privacy:
- **Only public or club-approved official circulars** are ingested.
- **Automated PII scrubbing** strips and redacts student register numbers (e.g., `41XXXX45`), personal email addresses, and personal phone numbers before documents reach the vector database.
- Private student databases (marks sheets, disciplinary registers, attendance logs) are strictly prohibited.

---

## 🚀 Quick Start & Usage

### 1. Prerequisites
Ensure you have Python 3.10+ installed along with document extraction dependencies:
```bash
pip install pypdf pdfplumber python-docx
```

### 2. Ingesting New Documents
1. Place raw official files (`.pdf`, `.docx`, `.txt`, `.json`) into the respective `data/raw/<category>/` directory following our naming convention:
   ```text
   [CATEGORY]_[AUTHORITY]_[ACAD_YEAR]_[TOPIC_SLUG]_[DATE_YYYYMMDD].[ext]
   ```
   *Examples:*
   - `ACAD_REGISTRAR_2026-27_ATTENDANCE_AND_SCHEDULE_POLICY_20261101.txt`
   - `EXAM_COE_2026-27_GRADING_CAE_AND_REVALUATION_RULES_20261101.txt`
   - `HOSTEL_ADMIN_2026-27_RULES_TIMINGS_AND_AMENITIES_20261101.txt`
   - `PLACE_CDC_2026-27_ELIGIBILITY_AND_UPGRADE_POLICY_20261101.txt`

2. Run the automated data cleaning and chunking pipeline:
   ```bash
   python scripts/clean_and_chunk.py
   ```

3. The pipeline will automatically:
   - Extract text and format tables.
   - Remove recurring university headers/footers and boilerplate.
   - Normalize Indian academic date formats to ISO-8601 standard (`YYYY-MM-DD`).
   - Redact personal information (PII).
   - Generate sliding-window overlapping semantic chunks with full metadata tags.
   - Update the master catalog at `data/metadata/doc_catalog.csv`.

---

## 🤝 Contributing FAQs
To add common student questions from WhatsApp or senior mentors:
1. Copy `data/raw/faqs_community/FAQ_BLANK_TEMPLATE.json`.
2. Add the question, realistic student slang/variations, the factual verified answer, validity date, and search tags.
3. Re-run `python scripts/clean_and_chunk.py`.

---

## 👥 Team
- **AI/ML Subgroup**: Data Engineering, RAG Pipeline, Prompt Engineering, Evaluation.
- **Web & App Development**: Official chat widget and platform integration.
- **Cloud & DevOps**: Azure deployment and vector database management.
- **Microsoft Club, Sathyabama Institute of Science and Technology**.
