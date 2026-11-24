# Sathya Assist - Knowledge Base Repository

This directory serves as the single source of truth for all campus documents and student FAQs ingested by the **Sathya Assist** RAG pipeline (Microsoft Club, Sathyabama).

---

## 1. Directory Structure

```text
data/
├── raw/                      # Immutable, source-of-truth documents (PDF, DOCX, TXT)
│   ├── academics/            # Academic calendars, working day schedules, curriculum regulations
│   ├── examinations/         # COE circulars, arrear rules, exam timetables, grade evaluation
│   ├── hostels/              # Mess timings, gate closing, outing pass rules, room allocation
│   ├── finance_fees/         # Tuition deadlines, exam fee circulars, transport fees, payment portals
│   ├── placements/           # CDC guidelines, eligibility criteria, internship and dream offer policies
│   ├── club_events/          # Microsoft Club & technical symposium circulars, hackathons, workshops
│   └── faqs_community/       # Crowdsourced & verified student Q&As (WhatsApp, seniors, mentorship)
│
├── processed/
│   ├── text/                 # Cleaned, standardized Markdown/Text documents (headers/footers stripped)
│   └── chunks/               # Chunked JSON files with rich metadata ready for embedding & vector store
│
└── metadata/
    ├── doc_catalog.csv       # Master catalog tracking doc provenance, validity, author, and hashes
    └── pii_audit_log.jsonl   # Audit log of any scrubbed student identifiers
```

---

## 2. Standardized Naming Convention

All raw and processed files **MUST** adhere to the following deterministic naming convention:

`[CATEGORY]_[AUTHORITY]_[ACAD_YEAR]_[TOPIC_SLUG]_[DATE_YYYYMMDD].[ext]`

### Category Codes:
- `ACAD`: Academics & Curriculum (Dean Academics, Registrar)
- `EXAM`: Examinations & Grading (Controller of Examinations - COE)
- `HOSTEL`: Hostel Administration & Wardens
- `FEES`: Accounts & Fee Section
- `PLACE`: Placement & Training Cell (CDC)
- `CLUB`: Student Clubs (Microsoft Club, Student Affairs)
- `FAQ`: Crowdsourced & Senior Verified FAQs

### Examples:
- `ACAD_REGISTRAR_2025-26_ODD_SEM_CALENDAR_20250615.pdf`
- `EXAM_COE_2025-26_ARREAR_REGISTRATION_PROCEDURE_20251020.pdf`
- `HOSTEL_WARDEN_2025-26_GENERAL_RULES_AND_GATE_TIMINGS_20250810.pdf`
- `PLACE_CDC_2025-26_CAMPUS_RECRUITMENT_POLICY_20250725.docx`
- `FAQ_MSCLUB_2025-26_FRESHERS_ONBOARDING_GUIDE_20250905.json`

---

## 3. Privacy & Compliance Rules (Zero PII Policy)

> **CRITICAL**: Sathya Assist is a public-facing assistant. Student confidentiality is non-negotiable.

1. **Permitted Documents**:
   - Official institutional circulars released to the public or general student body.
   - Guidelines, rules, regulations, contact directories, and club announcements.
   - Verified generic FAQ compilations.

2. **Strictly Prohibited Documents (NEVER Ingest)**:
   - Student nominal rolls or batch mark sheets containing names, register numbers, or grades.
   - Disciplinary action orders mentioning individual students.
   - Fee defaulter lists or scholarship sanction lists with student details.
   - Private phone numbers of student office bearers unless explicitly designated for public club queries.

3. **Automated Scrubbing**:
   - The data cleaning script automatically runs regex scrubbers against Register Numbers (e.g. `4[0-9]{7}` or `1[0-9]{7}`), personal emails, and phone numbers.
