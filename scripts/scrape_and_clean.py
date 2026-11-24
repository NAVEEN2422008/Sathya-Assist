"""
Sathya Assist - Official Data Scraping, Verification & Cleaning Engine
Microsoft Club, Sathyabama Institute of Science and Technology

ZERO-HALLUCINATION DIRECTIVE:
Fetches ONLY genuine, verifiable data from official Sathyabama domains (sathyabama.ac.in),
calculates SHA-256 provenance hashes, extracts structured text/tables, and logs full metadata
to data/data_manifest.json.
"""

import os
import re
import sys
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
import pdfplumber

# Institutional boilerplate phrases to strip out
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

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

MANIFEST_PATH = Path("data/data_manifest.json")


def compute_sha256(filepath: Path) -> str:
    """Computes SHA-256 checksum of a file."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def load_manifest() -> Dict[str, Any]:
    """Loads existing manifest or initializes empty structure."""
    if MANIFEST_PATH.exists():
        try:
            with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "metadata_version": "1.0.0",
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "total_documents": 0,
        "documents": []
    }


def save_manifest(manifest: Dict[str, Any]):
    """Persists data manifest to disk."""
    manifest["last_updated"] = datetime.now(timezone.utc).isoformat()
    manifest["total_documents"] = len(manifest["documents"])
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)


def clean_text_content(raw_text: str) -> str:
    """Cleans repetitive boilerplate, normalizes whitespace, and fixes broken hyphens."""
    text = raw_text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\xa0", " ").replace("\u200b", "")

    # Fix broken hyphenated line wraps (e.g. atten-\ndance -> attendance)
    text = re.sub(r"(\w+)-\n(\w+)", r"\1\2", text)

    lines = text.split("\n")
    cleaned_lines = []
    for line in lines:
        line_str = line.strip()
        is_boilerplate = any(re.search(pat, line_str) for pat in BOILERPLATE_PATTERNS)
        if not is_boilerplate:
            cleaned_lines.append(line)

    text = "\n".join(cleaned_lines)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text


def extract_pdf_tables_and_text(pdf_path: Path) -> str:
    """
    Extracts text and tables from a PDF using pdfplumber, converting
    tables into clean markdown tables.
    """
    extracted_sections = []
    with pdfplumber.open(pdf_path) as pdf:
        for p_idx, page in enumerate(pdf.pages, start=1):
            page_text = page.extract_text(layout=True)
            tables = page.extract_tables()

            extracted_sections.append(f"### Page {p_idx}\n")

            if tables:
                for table in tables:
                    md_rows = []
                    # Filter out completely empty rows
                    filtered_rows = [row for row in table if any(row)]
                    if not filtered_rows:
                        continue

                    # Header row
                    headers = [str(c or "").strip().replace("\n", " ") for c in filtered_rows[0]]
                    md_rows.append("| " + " | ".join(headers) + " |")
                    md_rows.append("| " + " | ".join(["---"] * len(headers)) + " |")

                    # Data rows
                    for row in filtered_rows[1:]:
                        cells = [str(c or "").strip().replace("\n", " ") for c in row]
                        md_rows.append("| " + " | ".join(cells) + " |")

                    extracted_sections.append("\n".join(md_rows) + "\n")

            if page_text:
                extracted_sections.append(clean_text_content(page_text))

    return "\n\n".join(extracted_sections)


def extract_html_content(html_content: str, source_url: str) -> Tuple[str, str]:
    """
    Extracts main content and title from an HTML string, stripping scripts,
    navigation headers, and footers.
    """
    soup = BeautifulSoup(html_content, "html.parser")

    # Extract title
    title = "Sathyabama Official Document"
    if soup.title and soup.title.string:
        title = soup.title.string.strip()
    elif soup.find("h1"):
        title = soup.find("h1").get_text(strip=True)

    # Decompose unwanted elements
    for tag in soup(["script", "style", "nav", "header", "footer", "aside", "form"]):
        tag.decompose()

    # Target content containers commonly used by Drupal / University CMS
    content_container = (
        soup.find("main") or
        soup.find("article") or
        soup.find("div", class_=re.compile(r"content|field-item|region-content|main-content", re.I)) or
        soup.body
    )

    if not content_container:
        content_container = soup

    # Convert tables to markdown tables
    for table in content_container.find_all("table"):
        rows = table.find_all("tr")
        if not rows:
            continue
        md_table = []
        # Header
        headers = [th.get_text(strip=True).replace("\n", " ") for th in rows[0].find_all(["th", "td"])]
        if headers:
            md_table.append("| " + " | ".join(headers) + " |")
            md_table.append("| " + " | ".join(["---"] * len(headers)) + " |")
            for r in rows[1:]:
                cells = [td.get_text(strip=True).replace("\n", " ") for td in r.find_all(["td", "th"])]
                if any(cells):
                    md_table.append("| " + " | ".join(cells) + " |")
            table.replace_with(soup.new_string("\n\n" + "\n".join(md_table) + "\n\n"))

    raw_text = content_container.get_text(separator="\n")
    cleaned_text = clean_text_content(raw_text)

    return title, cleaned_text


def fetch_and_process_url(
    url: str,
    category: str,
    document_id: str,
    applicable_academic_year: str = "2026-2027",
    official_contact_office: str = "University Administration",
    custom_title: Optional[str] = None
) -> Dict[str, Any]:
    """
    Downloads, extracts, cleans, and indexes an official Sathyabama URL or PDF.
    Validates that the source belongs to sathyabama.ac.in.
    """
    parsed = urlparse(url)
    if "sathyabama.ac.in" not in parsed.netloc:
        raise ValueError(f"Strict Security Directive: Only sathyabama.ac.in URLs are permitted. Given: {url}")

    raw_cat_dir = Path("data/raw") / category
    proc_cat_dir = Path("data/processed") / category
    raw_cat_dir.mkdir(parents=True, exist_ok=True)
    proc_cat_dir.mkdir(parents=True, exist_ok=True)

    access_time = datetime.now(timezone.utc).isoformat()
    response = requests.get(url, headers=DEFAULT_HEADERS, timeout=25)
    response.raise_for_status()

    content_type = response.headers.get("Content-Type", "").lower()
    is_pdf = url.lower().endswith(".pdf") or "application/pdf" in content_type

    if is_pdf:
        raw_filename = f"{document_id}.pdf"
        raw_filepath = raw_cat_dir / raw_filename
        with open(raw_filepath, "wb") as f:
            f.write(response.content)

        file_hash = compute_sha256(raw_filepath)
        cleaned_text = extract_pdf_tables_and_text(raw_filepath)
        title = custom_title or document_id.replace("_", " ").title()

    else:
        raw_filename = f"{document_id}.html"
        raw_filepath = raw_cat_dir / raw_filename
        with open(raw_filepath, "w", encoding="utf-8", errors="ignore") as f:
            f.write(response.text)

        file_hash = compute_sha256(raw_filepath)
        extracted_title, cleaned_text = extract_html_content(response.text, url)
        title = custom_title or extracted_title

    # Save cleaned processed markdown with frontmatter
    proc_filename = f"{document_id}.md"
    proc_filepath = proc_cat_dir / proc_filename

    frontmatter = (
        f"---\n"
        f"document_id: \"{document_id}\"\n"
        f"source_title: \"{title}\"\n"
        f"source_url: \"{url}\"\n"
        f"access_timestamp: \"{access_time}\"\n"
        f"applicable_academic_year: \"{applicable_academic_year}\"\n"
        f"category: \"{category}\"\n"
        f"official_contact_office: \"{official_contact_office}\"\n"
        f"sha256_hash: \"{file_hash}\"\n"
        f"---\n\n"
    )

    with open(proc_filepath, "w", encoding="utf-8") as f:
        f.write(frontmatter + cleaned_text)

    # Provenance record entry
    provenance_record = {
        "document_id": document_id,
        "source_title": title,
        "source_url": url,
        "access_timestamp": access_time,
        "applicable_academic_year": applicable_academic_year,
        "category": category,
        "official_contact_office": official_contact_office,
        "file_hash_sha256": file_hash,
        "raw_file_path": str(raw_filepath).replace("\\", "/"),
        "processed_file_path": str(proc_filepath).replace("\\", "/")
    }

    # Update manifest
    manifest = load_manifest()
    # Update if already exists, else append
    existing_idx = next((i for i, d in enumerate(manifest["documents"]) if d["document_id"] == document_id), None)
    if existing_idx is not None:
        manifest["documents"][existing_idx] = provenance_record
    else:
        manifest["documents"].append(provenance_record)

    save_manifest(manifest)
    print(f"[Success] Ingested {document_id} from {url} -> {proc_filepath}")
    return provenance_record


if __name__ == "__main__":
    print("Sathya Assist Scraping & Cleaning Engine initialized.")
    print("Ready for automated navigational retrieval.")
