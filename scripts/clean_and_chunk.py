"""
Sathya Assist - Data Cleaning and Chunking Pipeline
Microsoft Club, Sathyabama Institute of Science and Technology

Extracts, cleans, anonymizes, chunks, and enriches campus documents (PDF, DOCX, TXT, JSON)
for Retrieval-Augmented Generation (RAG).
"""

import os
import re
import sys
import json
import hashlib
import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Third-party document extractors
try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

try:
    import docx
except ImportError:
    docx = None


# -----------------------------------------------------------------------------
# 1. CONSTANTS & REGEX PATTERNS
# -----------------------------------------------------------------------------

# Institutional boilerplate phrases to eliminate
BOILERPLATE_PATTERNS = [
    r"(?i)sathyabama\s+institute\s+of\s+science\s+and\s+technology",
    r"(?i)\(deemed\s+to\s+be\s+university\)",
    r"(?i)category\s*-\s*1\s+university\s+by\s+ugc",
    r"(?i)accredited\s+with\s+['\"]?a\+{1,2}['\"]?\s+grade\s+by\s+naac",
    r"(?i)jeppiaar\s+nagar,\s*rajiv\s+gandhi\s+salai,\s*chennai\s*-\s*600\s*119",
    r"(?i)tamil\s*nadu,\s*india\.?\s*www\.sathyabama\.ac\.in",
    r"(?i)page\s+\d+\s+of\s+\d+",
    r"(?i)page\s+\d+",
    r"^[-=_*~]{3,}$",
]

# PII Patterns for redaction (Strict Zero-PII Policy)
# Sathyabama student register numbers: typically 8 digits, starting with 3 or 4 (e.g., 41110001, 42110250)
PII_REGISTER_NUMBER_PATTERN = r"\b[34]\d{7}\b"
# Indian 10-digit mobile numbers with optional country code (+91)
PII_PHONE_PATTERN = r"(?:\+91[\-\s]?)?[6-9]\d{9}\b"
# Personal student email IDs (e.g., 41110001@sathyabama.ac.in or personal gmail/yahoo)
PII_STUDENT_EMAIL_PATTERN = r"\b[34]\d{7}@sathyabama\.ac\.in\b"
PII_GENERIC_PERSONAL_EMAIL = r"\b[A-Za-z0-9._%+-]+@(?!sathyabama\.ac\.in|microsoft\.com)[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"

# Category mapping lookup from file prefix or manifest category
CATEGORY_MAP = {
    "ACAD": "Academics",
    "EXAM": "Examinations",
    "HOSTEL": "Hostel Life",
    "TRANSPORT": "Transport & Bus",
    "FEES": "Fees & Finance",
    "FEE": "Fees & Finance",
    "PLACE": "Placements & Training",
    "CLUB": "Club Events",
    "FAQ": "Student FAQs",
    "academics": "Academics",
    "exams": "Examinations",
    "hostels": "Hostel Life",
    "fees": "Fees & Finance",
    "placements": "Placements & Training",
    "clubs": "Club Events",
}


# -----------------------------------------------------------------------------
# 2. DOCUMENT EXTRACTION ENGINE
# -----------------------------------------------------------------------------

class DocumentExtractor:
    """Extracts raw text from PDF, DOCX, TXT, and JSON files."""

    @staticmethod
    def extract_from_pdf(filepath: Path) -> str:
        """Extracts text from PDF prioritizing pdfplumber for layout, falling back to pypdf."""
        text_parts = []

        if pdfplumber is not None:
            try:
                with pdfplumber.open(filepath) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text(layout=True)
                        if page_text:
                            text_parts.append(page_text)
                if text_parts:
                    return "\n\n".join(text_parts)
            except Exception as e:
                print(f"[Warning] pdfplumber failed on {filepath.name} ({e}), trying pypdf...")

        if PdfReader is not None:
            try:
                reader = PdfReader(str(filepath))
                for page in reader.pages:
                    extract = page.extract_text()
                    if extract:
                        text_parts.append(extract)
                return "\n\n".join(text_parts)
            except Exception as e:
                print(f"[Error] pypdf also failed on {filepath.name}: {e}")

        return ""

    @staticmethod
    def extract_from_docx(filepath: Path) -> str:
        """Extracts paragraphs and tables from a DOCX file."""
        if docx is None:
            raise ImportError("python-docx is not installed.")

        doc = docx.Document(str(filepath))
        parts = []

        # Extract paragraphs
        for p in doc.paragraphs:
            text = p.text.strip()
            if text:
                parts.append(text)

        # Extract tables formatted cleanly
        for table in doc.tables:
            table_lines = []
            for row in table.rows:
                cells = [cell.text.strip().replace("\n", " ") for cell in row.cells]
                if any(cells):
                    table_lines.append(" | ".join(cells))
            if table_lines:
                parts.append("\n" + "\n".join(table_lines) + "\n")

        return "\n\n".join(parts)

    @staticmethod
    def extract_from_txt(filepath: Path) -> str:
        """Reads plain text / markdown files with UTF-8 encoding."""
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    @classmethod
    def extract(cls, filepath: Path) -> str:
        ext = filepath.suffix.lower()
        if ext == ".pdf":
            return cls.extract_from_pdf(filepath)
        elif ext in [".docx", ".doc"]:
            return cls.extract_from_docx(filepath)
        elif ext in [".txt", ".md"]:
            return cls.extract_from_txt(filepath)
        elif ext in [".html", ".htm"]:
            try:
                from bs4 import BeautifulSoup
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    soup = BeautifulSoup(f.read(), "html.parser")
                for s in soup(["script", "style", "nav", "header", "footer", "aside", "form"]):
                    s.decompose()
                container = (
                    soup.find("main")
                    or soup.find("article")
                    or soup.find("div", class_=re.compile(r"content|field-item|region-content|main-content", re.I))
                    or soup.body
                    or soup
                )
                for table in container.find_all("table"):
                    rows = table.find_all("tr")
                    if not rows:
                        continue
                    md_table = []
                    headers = [th.get_text(strip=True).replace("\n", " ") for th in rows[0].find_all(["th", "td"])]
                    if headers:
                        md_table.append("| " + " | ".join(headers) + " |")
                        md_table.append("| " + " | ".join(["---"] * len(headers)) + " |")
                        for r in rows[1:]:
                            cells = [td.get_text(strip=True).replace("\n", " ") for td in r.find_all(["td", "th"])]
                            if any(cells):
                                md_table.append("| " + " | ".join(cells) + " |")
                        table.replace_with(soup.new_string("\n\n" + "\n".join(md_table) + "\n\n"))
                return container.get_text(separator="\n")
            except Exception:
                return cls.extract_from_txt(filepath)
        elif ext == ".json":
            return cls.extract_from_txt(filepath)
        else:
            raise ValueError(f"Unsupported file format: {ext}")


# -----------------------------------------------------------------------------
# 3. TEXT CLEANING, NORMALIZATION & PII SCRUBBING
# -----------------------------------------------------------------------------

class TextCleaner:
    """Removes noise, normalizes formatting & dates, and redacts sensitive PII."""

    @classmethod
    def clean(cls, raw_text: str) -> Tuple[str, List[str]]:
        """
        Cleans the document text.
        Returns:
            Tuple[cleaned_text, list_of_redactions_audit]
        """
        audit_log = []
        text = raw_text

        # 1. Fix encoding and whitespace artifacts
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = text.replace("\xa0", " ")  # non-breaking spaces
        text = text.replace("\u200b", "")  # zero-width space

        # 2. Fix hyphenated line breaks (e.g., 'submis-\nsion' -> 'submission')
        text = re.sub(r"(\w+)-\n(\w+)", r"\1\2", text)

        # 3. Strip boilerplate headers/footers line by line
        lines = text.split("\n")
        cleaned_lines = []
        for line in lines:
            line_str = line.strip()
            is_boilerplate = False
            for pattern in BOILERPLATE_PATTERNS:
                if re.search(pattern, line_str):
                    is_boilerplate = True
                    break
            if not is_boilerplate:
                cleaned_lines.append(line)
        text = "\n".join(cleaned_lines)

        # 4. Normalize dates to standard ISO-like readable format
        text = cls.normalize_dates(text)

        # 5. PII Redaction
        text, pii_logs = cls.redact_pii(text)
        audit_log.extend(pii_logs)

        # 6. Compress excessive vertical whitespace
        text = re.sub(r"\n{3,}", "\n\n", text).strip()

        return text, audit_log

    @staticmethod
    def normalize_dates(text: str) -> str:
        """
        Detects common Indian academic date notations and normalizes them.
        e.g., '14.03.2025', '14/03/2025', '14-03-2025', '14th March 2025' -> '2025-03-14 (14 March 2025)'
        """
        # Match DD/MM/YYYY or DD-MM-YYYY or DD.MM.YYYY
        def ddmmyyyy_repl(match):
            day, sep, month, _, year = match.groups()
            try:
                d = int(day)
                m = int(month)
                y = int(year)
                if 1 <= d <= 31 and 1 <= m <= 12 and 2020 <= y <= 2035:
                    dt = datetime(y, m, d)
                    return dt.strftime("%Y-%m-%d")
            except Exception:
                pass
            return match.group(0)

        pattern_slash = r"\b(0?[1-9]|[12]\d|3[01])([\/\.\-])(0?[1-9]|1[0-2])([\/\.\-])(202[4-9]|203\d)\b"
        text = re.sub(pattern_slash, ddmmyyyy_repl, text)

        # Match '15th August 2025' or '15 August 2025'
        month_names = "January|February|March|April|May|June|July|August|September|October|November|December"
        pattern_words = rf"\b(\d{{1,2}})(?:st|nd|rd|th)?\s+({month_names})\s+(202[4-9]|203\d)\b"

        def word_date_repl(match):
            day, month, year = match.groups()
            try:
                dt = datetime.strptime(f"{day} {month} {year}", "%d %B %Y")
                return f"{dt.strftime('%Y-%m-%d')} ({day} {month} {year})"
            except Exception:
                return match.group(0)

        text = re.sub(pattern_words, word_date_repl, text, flags=re.IGNORECASE)
        return text

    @staticmethod
    def redact_pii(text: str) -> Tuple[str, List[str]]:
        """Redacts register numbers, private student phone numbers, and emails."""
        redactions = []

        # Redact student register numbers
        def mask_reg(match):
            reg = match.group(0)
            redactions.append(f"Redacted Register Number: {reg[:2]}XXXX{reg[-2:]}")
            return "[STUDENT_REG_NO_REDACTED]"

        text = re.sub(PII_REGISTER_NUMBER_PATTERN, mask_reg, text)

        # Redact personal student emails
        def mask_email(match):
            email = match.group(0)
            redactions.append(f"Redacted Student Email: {email}")
            return "[STUDENT_EMAIL_REDACTED]"

        text = re.sub(PII_STUDENT_EMAIL_PATTERN, mask_email, text)
        text = re.sub(PII_GENERIC_PERSONAL_EMAIL, mask_email, text)

        # Redact mobile numbers (excluding standard college landline formats if any)
        def mask_phone(match):
            phone = match.group(0)
            redactions.append(f"Redacted Phone Number: {phone[:3]}XXXX{phone[-3:]}")
            return "[PHONE_REDACTED]"

        text = re.sub(PII_PHONE_PATTERN, mask_phone, text)

        return text, redactions


# -----------------------------------------------------------------------------
# 4. METADATA EXTRACTION & SCHEMA TAGGING
# -----------------------------------------------------------------------------

class MetadataExtractor:
    """Loads authoritative metadata from data_manifest.json with filename fallback."""

    _manifest_cache: Optional[Dict[str, Dict[str, Any]]] = None

    @classmethod
    def _load_manifest_index(cls, manifest_path: Path = Path("data/metadata/data_manifest.json")) -> Dict[str, Dict[str, Any]]:
        if cls._manifest_cache is not None:
            return cls._manifest_cache
        cls._manifest_cache = {}
        if manifest_path.exists():
            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for doc in data.get("documents", []):
                    doc_id = doc.get("document_id")
                    if doc_id:
                        cls._manifest_cache[doc_id] = doc
            except Exception as e:
                print(f"[Warning] Could not read manifest {manifest_path}: {e}")
        return cls._manifest_cache

    @classmethod
    def parse_filename(cls, filepath: Path) -> Dict[str, Any]:
        """
        Resolves metadata from data_manifest.json first; falls back to filename convention:
        [CATEGORY]_[AUTHORITY]_[ACAD_YEAR]_[TOPIC_SLUG]_[DATE_YYYYMMDD].[ext]
        """
        stem = filepath.stem
        tokens = stem.split("_")

        meta = {
            "source_filename": filepath.name,
            "document_id": stem,
            "category_code": tokens[0].upper() if tokens else "GENERAL",
            "category": CATEGORY_MAP.get(tokens[0].upper(), "General Information") if tokens else "General Information",
            "department": "Campus Administration",
            "academic_year": "2026-2027",
            "topic": stem.replace("_", " ").title(),
            "publication_date": None,
            "valid_until": "End of Academic Year",
            "target_audience": "All Students",
            "source_url": None,
            "source_title": stem.replace("_", " ").title(),
        }

        manifest_index = cls._load_manifest_index()
        if stem in manifest_index:
            m = manifest_index[stem]
            raw_cat = m.get("category", "")
            meta["category"] = CATEGORY_MAP.get(raw_cat, raw_cat.title() if raw_cat else meta["category"])
            meta["department"] = m.get("official_contact_office", meta["department"])
            meta["academic_year"] = m.get("applicable_academic_year", meta["academic_year"])
            meta["source_url"] = m.get("source_url")
            meta["source_title"] = m.get("source_title", meta["source_title"])
            meta["topic"] = m.get("source_title", meta["topic"])
            ts = m.get("access_timestamp")
            if ts:
                meta["publication_date"] = ts[:10]
        elif len(tokens) >= 5 and re.match(r"^\d{4}-\d{2,4}$", tokens[2]):
            cat_code = tokens[0].upper()
            dept_code = tokens[1].upper()
            acad_yr = tokens[2]
            topic = " ".join(tokens[3:-1]).replace("-", " ").title()
            date_str = tokens[-1]

            meta["category_code"] = cat_code
            meta["category"] = CATEGORY_MAP.get(cat_code, "General Information")
            meta["department"] = dept_code
            meta["academic_year"] = acad_yr
            meta["topic"] = topic

            if re.match(r"^\d{8}$", date_str):
                try:
                    dt = datetime.strptime(date_str, "%Y%m%d")
                    meta["publication_date"] = dt.strftime("%Y-%m-%d")
                except ValueError:
                    pass

        # Calculate file hash for provenance
        hasher = hashlib.sha256()
        with open(filepath, "rb") as f:
            hasher.update(f.read())
        meta["file_hash_sha256"] = hasher.hexdigest()[:16]

        return meta


# -----------------------------------------------------------------------------
# 5. SEMANTIC CHUNKING ENGINE
# -----------------------------------------------------------------------------

class SemanticChunker:
    """Chunks text into token/character bounded chunks with semantic awareness and overlap."""

    def __init__(self, target_chunk_size: int = 1200, overlap_size: int = 200):
        self.target_chunk_size = target_chunk_size
        self.overlap_size = overlap_size

    def chunk_document(self, text: str, base_metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Splits document text into rich chunk dictionaries."""
        paragraphs = text.split("\n\n")
        chunks = []
        current_chunk = []
        current_length = 0
        current_section = "General Overview"

        for p in paragraphs:
            p = p.strip()
            if not p:
                continue

            # Detect section heading
            if (p.startswith("#") or (len(p) < 80 and p.isupper()) or
                re.match(r"^(Section|Clause|Rule|Part)\s+\d+", p, re.IGNORECASE)):
                current_section = p.lstrip("#").strip()

            p_len = len(p)

            if current_length + p_len > self.target_chunk_size and current_chunk:
                chunk_str = "\n\n".join(current_chunk)
                chunks.append((chunk_str, current_section))
                
                # Keep sliding window overlap
                overlap_text = current_chunk[-1] if len(current_chunk[-1]) < self.overlap_size else current_chunk[-1][-self.overlap_size:]
                current_chunk = [overlap_text, p]
                current_length = len(overlap_text) + p_len
            else:
                current_chunk.append(p)
                current_length += p_len

        if current_chunk:
            chunk_str = "\n\n".join(current_chunk)
            chunks.append((chunk_str, current_section))

        total_chunks = len(chunks)
        chunk_objects = []

        for idx, (content, section) in enumerate(chunks):
            chunk_meta = dict(base_metadata)
            chunk_id = f"{base_metadata['document_id']}_c{idx+1:03d}"
            
            chunk_meta.update({
                "chunk_id": chunk_id,
                "chunk_index": idx + 1,
                "total_chunks": total_chunks,
                "section_heading": section,
                "char_count": len(content),
                "estimated_tokens": int(len(content.split()) * 1.3),
            })

            chunk_objects.append({
                "chunk_id": chunk_id,
                "content": content,
                "metadata": chunk_meta
            })

        return chunk_objects


# -----------------------------------------------------------------------------
# 6. FAQ JSON PROCESSOR
# -----------------------------------------------------------------------------

def process_faq_file(filepath: Path) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Specialized handler for student FAQ templates (JSON format)."""
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    meta = MetadataExtractor.parse_filename(filepath)
    category = data.get("category", meta.get("category", "Student FAQs"))
    department = data.get("department", meta.get("department", "Student Affairs"))
    academic_year = data.get("academic_year", meta.get("academic_year", "2025-2026"))
    faqs = data.get("faqs", [])

    chunk_objects = []
    total = len(faqs)

    for idx, item in enumerate(faqs):
        q = item.get("question", "")
        variations = item.get("student_query_variations", [])
        a = item.get("official_answer", "")
        verified_by = item.get("verified_by", "Microsoft Club Knowledge Team")
        validity = item.get("valid_until", "Current Academic Year")
        tags = item.get("tags", [])

        # Format content for optimal LLM retrieval
        variations_str = ", ".join([f'"{v}"' for v in variations]) if variations else "None"
        content = (
            f"Question: {q}\n"
            f"Common Student Phrasings: {variations_str}\n"
            f"Answer: {a}\n"
            f"Verified Authority: {verified_by}\n"
            f"Validity: {validity}\n"
            f"Keywords: {', '.join(tags)}"
        )

        chunk_id = f"{meta['document_id']}_faq{idx+1:03d}"
        item_meta = dict(meta)
        item_meta.update({
            "chunk_id": chunk_id,
            "chunk_index": idx + 1,
            "total_chunks": total,
            "category": category,
            "department": department,
            "academic_year": academic_year,
            "section_heading": f"FAQ: {q[:50]}",
            "tags": tags,
            "char_count": len(content),
            "estimated_tokens": int(len(content.split()) * 1.3)
        })

        chunk_objects.append({
            "chunk_id": chunk_id,
            "content": content,
            "metadata": item_meta
        })

    return chunk_objects, meta


# -----------------------------------------------------------------------------
# 7. MAIN ORCHESTRATION PIPELINE
# -----------------------------------------------------------------------------

def process_all_documents(
    raw_dir: Path = Path("data/raw"),
    processed_dir: Path = Path("data/processed"),
    chunks_dir: Path = Path("data/chunks"),
    metadata_dir: Path = Path("data/metadata")
):
    """Processes all raw documents and generates categorized cleaned text, chunk JSONs, and catalog."""
    raw_dir = Path(raw_dir)
    processed_dir = Path(processed_dir)
    chunks_dir = Path(chunks_dir)
    metadata_dir = Path(metadata_dir)

    processed_dir.mkdir(parents=True, exist_ok=True)
    chunks_dir.mkdir(parents=True, exist_ok=True)
    metadata_dir.mkdir(parents=True, exist_ok=True)

    catalog_entries = []
    all_pii_audit = []
    chunker = SemanticChunker()

    files = [f for f in raw_dir.rglob("*") if f.is_file() and not f.name.startswith(".")]

    if not files:
        print(f"[Info] No files found in {raw_dir}. Place raw files in data/raw/<category>/")
        return

    print(f"=== Starting Sathya Assist Document Cleaning Pipeline ===")
    print(f"Found {len(files)} file(s) across {raw_dir}")

    for file in files:
        print(f"\n[Processing] {file.name}")
        base_meta = MetadataExtractor.parse_filename(file)

        # Specialized FAQ handler
        if file.suffix.lower() == ".json":
            try:
                chunks, doc_meta = process_faq_file(file)
                chunks_file = chunks_dir / f"{doc_meta['document_id']}_chunks.json"
                with open(chunks_file, "w", encoding="utf-8") as f:
                    json.dump(chunks, f, indent=2, ensure_ascii=False)

                catalog_entries.append({
                    "document_id": doc_meta["document_id"],
                    "source_filename": file.name,
                    "category": doc_meta["category"],
                    "department": doc_meta["department"],
                    "academic_year": doc_meta["academic_year"],
                    "chunks_count": len(chunks),
                    "file_hash": doc_meta["file_hash_sha256"],
                    "status": "Processed (FAQ)"
                })
                print(f"  -> Generated {len(chunks)} FAQ chunk(s) -> {chunks_file.name}")
                continue
            except Exception as e:
                print(f"  [Error] Failed processing FAQ JSON {file.name}: {e}")
                continue

        # General Document (PDF, DOCX, TXT, HTML)
        try:
            raw_text = DocumentExtractor.extract(file)
            cleaned_text, pii_audit = TextCleaner.clean(raw_text)

            for item in pii_audit:
                all_pii_audit.append({"file": file.name, "detail": item})

            # Save cleaned text categorized under data/processed/<category_folder>/
            category_folder = file.parent.name if file.parent.name in ["academics", "exams", "hostels", "placements", "fees", "clubs"] else "general"
            target_text_dir = processed_dir / category_folder
            target_text_dir.mkdir(parents=True, exist_ok=True)
            cleaned_md_file = target_text_dir / f"{base_meta['document_id']}.md"

            # If raw extraction is minimal (e.g., JS-rendered SPA shell) and a verified processed .md exists, use it
            if len(cleaned_text.strip()) < 100 and cleaned_md_file.exists():
                existing_md = cleaned_md_file.read_text(encoding="utf-8")
                cleaned_text = re.sub(r"^---\n.*?\n---\n+", "", existing_md, flags=re.DOTALL).strip()
                print(f"  -> Preserved verified SPA content from {cleaned_md_file.name}")
            elif not cleaned_text.strip():
                print(f"  [Warning] Extracted text is empty for {file.name}. Skipping.")
                continue
            else:
                with open(cleaned_md_file, "w", encoding="utf-8") as f:
                    f.write(f"<!--\nMetadata:\n")
                    f.write(f"  Document ID: {base_meta['document_id']}\n")
                    f.write(f"  Category: {base_meta['category']}\n")
                    f.write(f"  Department: {base_meta['department']}\n")
                    f.write(f"  Academic Year: {base_meta['academic_year']}\n")
                    f.write(f"  Publication Date: {base_meta['publication_date']}\n")
                    f.write(f"-->\n\n")
                    f.write(cleaned_text)

            # Chunk document
            chunks = chunker.chunk_document(cleaned_text, base_meta)

            chunks_file = chunks_dir / f"{base_meta['document_id']}_chunks.json"
            with open(chunks_file, "w", encoding="utf-8") as f:
                json.dump(chunks, f, indent=2, ensure_ascii=False)

            catalog_entries.append({
                "document_id": base_meta["document_id"],
                "source_filename": file.name,
                "category": base_meta["category"],
                "department": base_meta["department"],
                "academic_year": base_meta["academic_year"],
                "chunks_count": len(chunks),
                "file_hash": base_meta["file_hash_sha256"],
                "status": "Processed"
            })

            print(f"  -> Cleaned text saved to: {cleaned_md_file.name}")
            print(f"  -> Generated {len(chunks)} chunk(s) -> {chunks_file.name}")

        except Exception as e:
            print(f"  [Error] Failed processing {file.name}: {e}")

    # Write Master Catalog CSV
    catalog_path = metadata_dir / "doc_catalog.csv"
    if catalog_entries:
        keys = catalog_entries[0].keys()
        with open(catalog_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(catalog_entries)
        print(f"\n[Master Catalog] Updated: {catalog_path}")

    # Write PII Audit log
    pii_log_path = metadata_dir / "pii_audit_log.jsonl"
    with open(pii_log_path, "a", encoding="utf-8") as f:
        for audit in all_pii_audit:
            audit["timestamp"] = datetime.now().isoformat()
            f.write(json.dumps(audit) + "\n")
    if all_pii_audit:
        print(f"[PII Audit] {len(all_pii_audit)} PII redactions recorded in {pii_log_path}")

    print("=== Pipeline Run Finished ===")


if __name__ == "__main__":
    process_all_documents()
