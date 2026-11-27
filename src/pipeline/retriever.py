"""
Sathya Assist - Hybrid Semantic & Keyword Retriever
Owner: Arjun (Retrieval & Vector Store Architect)

Queries the persisted ChromaDB collection with category alias normalization
(INC-003 mitigation), lexical keyword boosting, and confidence thresholding.
"""

import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import chromadb

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline.ingest import CHROMA_DIR, COLLECTION_NAME

# Normalizes user/API category filters across document chunks and verified_faqs.json
CATEGORY_ALIASES: Dict[str, List[str]] = {
    "academics": ["Academics"],
    "academic": ["Academics"],
    "exams": ["Examinations"],
    "exam": ["Examinations"],
    "examinations": ["Examinations"],
    "hostels": ["Hostel Life", "Hostels", "Transport"],
    "hostel": ["Hostel Life", "Hostels"],
    "transport": ["Hostel Life", "Transport"],
    "placements": ["Placements & Training", "Placements"],
    "placement": ["Placements & Training", "Placements"],
    "cdc": ["Placements & Training", "Placements"],
    "fees": ["Fees & Finance", "Fees"],
    "fee": ["Fees & Finance", "Fees"],
}

STOPWORDS = {
    "what", "is", "the", "for", "and", "or", "in", "on", "to", "of", "a", "an",
    "are", "how", "can", "i", "do", "does", "when", "where", "who", "my", "me",
    "sathyabama", "students", "student", "college", "university", "there", "if",
}


def _tokenize_keywords(text: str) -> List[str]:
    tokens = re.findall(r"[a-z0-9\.]+", text.lower())
    return [t for t in tokens if len(t) > 1 and t not in STOPWORDS]


class SathyaRetriever:
    """Hybrid retriever over ChromaDB with metadata filtering and lexical boost."""

    def __init__(
        self,
        chroma_dir: Path = CHROMA_DIR,
        collection_name: str = COLLECTION_NAME,
    ):
        self.chroma_dir = Path(chroma_dir)
        self.collection_name = collection_name
        self._client = chromadb.PersistentClient(path=str(self.chroma_dir))
        self._collection = self._client.get_collection(name=self.collection_name)

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        category: Optional[str] = None,
        min_score: float = 0.28,
    ) -> List[Dict[str, Any]]:
        """
        Retrieves top_k relevant chunks for a query.
        Returns a list of dicts: {chunk_id, content, metadata, score, semantic_score, keyword_boost}.
        """
        if not query or not query.strip():
            return []

        where_filter = None
        if category:
            cats = CATEGORY_ALIASES.get(category.strip().lower())
            if cats:
                where_filter = {"category": {"$in": cats}}

        fetch_n = min(max(top_k * 3, 10), self._collection.count() or 10)
        res = self._collection.query(
            query_texts=[query],
            n_results=fetch_n,
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )

        ids = res.get("ids", [[]])[0]
        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        dists = res.get("distances", [[]])[0]

        q_keywords = _tokenize_keywords(query)
        candidates: List[Dict[str, Any]] = []

        for cid, doc, meta, dist in zip(ids, docs, metas, dists):
            semantic_score = max(0.0, 1.0 - float(dist))
            doc_lower = doc.lower()

            kw_boost = 0.0
            if q_keywords:
                hits = sum(1 for kw in q_keywords if kw in doc_lower)
                kw_boost = min(0.15, (hits / len(q_keywords)) * 0.15)

            # Domain alignment boost when query clearly signals a specific campus domain
            domain_boost = 0.0
            cat_val = str(meta.get("category", "")).lower()
            if any(k in query.lower() for k in ["fee", "tuition", "payment", "marksheet", "transcript", "cost", "rupees", "rs."]):
                if "fee" in cat_val:
                    domain_boost = 0.20
            elif any(k in query.lower() for k in ["hostel", "curfew", "outing", "warden", "mess", "laundry"]):
                if "hostel" in cat_val:
                    domain_boost = 0.20
            elif any(k in query.lower() for k in ["bus", "transport", "shuttle"]):
                if "transport" in cat_val or "hostel" in cat_val:
                    domain_boost = 0.20
            elif any(k in query.lower() for k in ["placement", "cdc", "dream", "super dream", "ctc", "package", "recruit", "companies", "company", "visited", "placed"]):
                if "placement" in cat_val:
                    domain_boost = 0.20
            elif any(k in query.lower() for k in ["exam", "cae", "revaluation", "arrear", "coe", "grade", "distinction"]):
                if "exam" in cat_val:
                    domain_boost = 0.20

            # Slight priority tie-breaker for curated verified FAQs
            faq_bonus = 0.03 if meta.get("record_type") == "verified_faq" else 0.0
            final_score = semantic_score + kw_boost + domain_boost + faq_bonus

            if final_score >= min_score:
                candidates.append({
                    "chunk_id": cid,
                    "content": doc,
                    "metadata": meta,
                    "score": round(final_score, 4),
                    "semantic_score": round(semantic_score, 4),
                    "keyword_boost": round(kw_boost, 4),
                })

        candidates.sort(key=lambda x: x["score"], reverse=True)
        return candidates[:top_k]


if __name__ == "__main__":
    retriever = SathyaRetriever()
    for test_q in [
        "What is the hostel curfew time?",
        "How much is duplicate marksheet fee?",
        "What is the Dream company CTC difference rule?",
    ]:
        hits = retriever.retrieve(test_q, top_k=2)
        print(f"\nQuery: {test_q}")
        for h in hits:
            print(f"  - [{h['score']}] {h['chunk_id']} ({h['metadata'].get('category')})")
