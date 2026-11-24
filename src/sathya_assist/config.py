"""
Configuration constants, paths, and patterns for Sathya Assist.
"""

from pathlib import Path

# Base Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
CHUNKS_DIR = DATA_DIR / "chunks"
METADATA_DIR = DATA_DIR / "metadata"
DOCS_DIR = PROJECT_ROOT / "docs"

# Category mappings
CATEGORIES = [
    "academics",
    "exams",
    "hostels",
    "placements",
    "fees",
    "clubs"
]

# Boilerplate patterns for Sathyabama circulars
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

# PII Patterns for redaction
PII_REGISTER_NUMBER_PATTERN = r"\b[34]\d{7}\b"
PII_PHONE_PATTERN = r"(?:\+91[\-\s]?)?[6-9]\d{9}\b"
PII_STUDENT_EMAIL_PATTERN = r"\b[34]\d{7}@sathyabama\.ac\.in\b"
