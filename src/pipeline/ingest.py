"""
Sathya Assist - Chunk Analysis & ChromaDB Vector Store Ingestion Pipeline
Owner: Arjun (Retrieval & Vector Store Architect)

Loads cleaned document chunks from data/chunks/ and verified FAQs from
data/processed/verified_faqs.json, analyzes text distributions, and upserts
them into a persistent ChromaDB collection with full metadata preservation.
"""

import json
import statistics
import sys
from pathlib import Path
from typing import Any, Dict, List

import chromadb

# Ensure project root is on sys.path when executed directly
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.sathya_assist.config import CHUNKS_DIR, DATA_DIR, PROCESSED_DIR

CHROMA_DIR = DATA_DIR / "chroma_db"
COLLECTION_NAME = "sathya_assist_kb"


def sanitize_metadata(meta: Dict[str, Any]) -> Dict[str, Any]:
    """Ensures all metadata values conform to ChromaDB scalar types (str, int, float, bool)."""
    clean: Dict[str, Any] = {}
    for k, v in meta.items():
        if v is None:
            continue
        if isinstance(v, (str, int, float, bool)):
            clean[k] = v
        elif isinstance(v, list):
            clean[k] = ", ".join(str(item) for item in v)
        else:
            clean[k] = str(v)
    return clean


def load_document_chunks(chunks_dir: Path = CHUNKS_DIR) -> List[Dict[str, Any]]:
    """Loads all chunk JSON files produced by scripts/clean_and_chunk.py."""
    records: List[Dict[str, Any]] = []
    for chunk_file in sorted(chunks_dir.glob("*_chunks.json")):
        with open(chunk_file, "r", encoding="utf-8") as f:
            items = json.load(f)
        for item in items:
            meta = dict(item.get("metadata", {}))
            meta["record_type"] = "document_chunk"
            records.append({
                "id": item["chunk_id"],
                "content": item["content"],
                "metadata": sanitize_metadata(meta),
            })
    return records


def load_verified_faqs(faq_path: Path = PROCESSED_DIR / "verified_faqs.json") -> List[Dict[str, Any]]:
    """Loads verified FAQ records and formats them as retrievable vector items."""
    if not faq_path.exists():
        return []
    with open(faq_path, "r", encoding="utf-8") as f:
        faqs = json.load(f)

    records: List[Dict[str, Any]] = []
    for faq in faqs:
        content = (
            f"Question: {faq['question']}\n"
            f"Verified Answer: {faq['verified_answer']}\n"
            f"Official Excerpt: {faq['verbatim_excerpt']}"
        )
        meta = {
            "chunk_id": faq["id"],
            "document_id": faq["source_document"],
            "source_filename": faq["source_document"],
            "source_url": faq["page_number_or_url"],
            "category": faq["category"],
            "academic_year": "2026-2027",
            "section_heading": f"Verified FAQ: {faq['question'][:60]}",
            "record_type": "verified_faq",
            "char_count": len(content),
            "estimated_tokens": int(len(content.split()) * 1.3),
        }
        records.append({
            "id": faq["id"],
            "content": content,
            "metadata": sanitize_metadata(meta),
        })
    return records


def analyze_distribution(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Computes chunk length and category distribution metrics."""
    lengths = [len(r["content"]) for r in records]
    by_category: Dict[str, int] = {}
    for r in records:
        cat = r["metadata"].get("category", "Unknown")
        by_category[cat] = by_category.get(cat, 0) + 1

    return {
        "total_records": len(records),
        "min_chars": min(lengths) if lengths else 0,
        "max_chars": max(lengths) if lengths else 0,
        "mean_chars": round(statistics.mean(lengths), 1) if lengths else 0,
        "median_chars": round(statistics.median(lengths), 1) if lengths else 0,
        "by_category": by_category,
    }


def ingest_to_chromadb(
    chroma_dir: Path = CHROMA_DIR,
    collection_name: str = COLLECTION_NAME,
    reset: bool = True,
) -> Dict[str, Any]:
    """Ingests all document chunks and verified FAQs into a persistent ChromaDB collection."""
    doc_records = load_document_chunks()
    faq_records = load_verified_faqs()
    all_records = doc_records + faq_records

    if not all_records:
        raise RuntimeError("No chunks or verified FAQs found to ingest.")

    stats = analyze_distribution(all_records)
    print("=== Sathya Assist Vector Store Ingestion (Arjun) ===")
    print(f"Loaded {len(doc_records)} document chunks + {len(faq_records)} verified FAQs = {len(all_records)} total records")
    print(f"Char distribution -> min: {stats['min_chars']}, max: {stats['max_chars']}, mean: {stats['mean_chars']}, median: {stats['median_chars']}")
    print(f"Category breakdown: {stats['by_category']}")

    chroma_dir.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(chroma_dir))

    if reset:
        try:
            client.delete_collection(name=collection_name)
        except Exception:
            pass

    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )

    batch_size = 50
    for i in range(0, len(all_records), batch_size):
        batch = all_records[i : i + batch_size]
        collection.upsert(
            ids=[r["id"] for r in batch],
            documents=[r["content"] for r in batch],
            metadatas=[r["metadata"] for r in batch],
        )

    count = collection.count()
    print(f"[Success] Persisted {count} vectors into ChromaDB at {chroma_dir} (collection='{collection_name}')")

    # Smoke test retrieval
    sample_query = "What is the hostel curfew time for students?"
    res = collection.query(query_texts=[sample_query], n_results=2)
    top_id = res["ids"][0][0] if res["ids"] and res["ids"][0] else None
    top_meta = res["metadatas"][0][0] if res["metadatas"] and res["metadatas"][0] else {}
    print(f"[Smoke Test] Query: '{sample_query}' -> Top Match: {top_id} (category={top_meta.get('category')}, doc={top_meta.get('document_id')})")

    return {
        "collection_name": collection_name,
        "persisted_count": count,
        "stats": stats,
        "smoke_test_top_id": top_id,
    }


if __name__ == "__main__":
    ingest_to_chromadb()
