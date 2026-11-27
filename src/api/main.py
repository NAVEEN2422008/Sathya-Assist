"""
Sathya Assist - FastAPI Backend & Streaming Chat API
Owner: Vikram (Full-Stack Integration & API Engineer)

Endpoints:
- GET  /api/health   : Service & ChromaDB readiness check
- POST /api/chat     : Grounded RAG Q&A (JSON or SSE streaming)
- POST /api/feedback : Student answer quality feedback logger
"""

import json
import os
import sys
import time
from collections import defaultdict, deque
from pathlib import Path
from typing import Any, Deque, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline.ingest import CHROMA_DIR, ingest_to_chromadb
from src.pipeline.rag_chain import SathyaRAGChain
from src.sathya_assist.config import DATA_DIR, METADATA_DIR

FEEDBACK_LOG = METADATA_DIR / "feedback.jsonl"
FRONTEND_DIR = PROJECT_ROOT / "frontend"

RATE_LIMIT_RPM = int(os.getenv("RATE_LIMIT_RPM", "30"))
_request_log: Dict[str, Deque[float]] = defaultdict(deque)

app = FastAPI(
    title="Sathya Assist API",
    description="Official RAG Campus Assistant API for Sathyabama Institute of Science and Technology (Microsoft Club)",
    version="1.0.0",
)

allowed_origins = [
    o.strip() for o in os.getenv("ALLOWED_ORIGINS", "*").split(",") if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if FRONTEND_DIR.exists():
    app.mount("/widget", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="widget")

_rag_chain: Optional[SathyaRAGChain] = None


def get_rag_chain() -> SathyaRAGChain:
    """Lazy-initializes ChromaDB (if needed) and returns the singleton SathyaRAGChain."""
    global _rag_chain
    if _rag_chain is None:
        if not CHROMA_DIR.exists():
            ingest_to_chromadb()
        _rag_chain = SathyaRAGChain()
    return _rag_chain


def check_rate_limit(client_ip: str) -> None:
    """Enforces a sliding-window per-IP rate limit."""
    now = time.time()
    window = _request_log[client_ip]
    while window and now - window[0] > 60.0:
        window.popleft()
    if len(window) >= RATE_LIMIT_RPM:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please wait a moment before sending more queries.",
        )
    window.append(now)


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=1000, description="Student question")
    category: Optional[str] = Field(None, description="Optional domain filter: academics, exams, hostels, transport, placements, fees")
    top_k: int = Field(4, ge=1, le=10)
    stream: bool = Field(False, description="Enable Server-Sent Events (SSE) streaming")


class Citation(BaseModel):
    document_id: str
    reference: str
    category: str
    score: float


class ChatResponse(BaseModel):
    query: str
    answer: str
    citations: List[Citation]
    fallback_triggered: bool
    guardrail_reason: Optional[str] = None
    latency_ms: float


class FeedbackRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    answer: str = Field(..., min_length=1, max_length=4000)
    rating: int = Field(..., ge=1, le=5, description="1 (unhelpful) to 5 (accurate)")
    comment: Optional[str] = Field(None, max_length=500)


@app.get("/api/health")
def health_check() -> Dict[str, Any]:
    chain = get_rag_chain()
    vector_count = chain.retriever._collection.count()
    return {
        "status": "ok",
        "service": "Sathya Assist API",
        "vectors_indexed": vector_count,
        "rate_limit_rpm": RATE_LIMIT_RPM,
    }


@app.post("/api/chat", response_model=ChatResponse)
def chat_endpoint(payload: ChatRequest, request: Request):
    client_ip = request.client.host if request.client else "unknown"
    check_rate_limit(client_ip)

    chain = get_rag_chain()
    result = chain.answer(
        query=payload.query,
        top_k=payload.top_k,
        category=payload.category,
    )

    if payload.stream:
        def event_stream():
            words = result["answer"].split(" ")
            for idx, word in enumerate(words):
                token = word if idx == 0 else " " + word
                yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
            yield f"data: {json.dumps({'type': 'metadata', 'citations': result['citations'], 'fallback_triggered': result['fallback_triggered'], 'latency_ms': result['latency_ms']})}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    return ChatResponse(
        query=result["query"],
        answer=result["answer"],
        citations=[Citation(**c) for c in result["citations"]],
        fallback_triggered=result["fallback_triggered"],
        guardrail_reason=result["guardrail_reason"],
        latency_ms=result["latency_ms"],
    )


@app.post("/api/feedback")
def submit_feedback(payload: FeedbackRequest) -> Dict[str, str]:
    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "query": payload.query,
        "answer": payload.answer,
        "rating": payload.rating,
        "comment": payload.comment,
    }
    with open(FEEDBACK_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return {"status": "recorded", "message": "Thank you for helping improve Sathya Assist."}
