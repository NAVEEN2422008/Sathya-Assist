"""
Sathya Assist - Automated Benchmark Evaluation & Red-Team Suite
Owner: Rahul (Lead QA, Red-Teamer & Evaluation Specialist)

Computes:
1. Retrieval Recall @ k (for factual queries)
2. Faithfulness / Answer Accuracy (keyword & fallback verification)
3. Citation Accuracy ([Source: ...] format & expected doc match)
4. Guardrail Pass Rate (PII blocks, prompt-injection blocks, out-of-scope fallbacks)
"""

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline.rag_chain import SathyaRAGChain

BENCHMARK_PATH = Path(__file__).resolve().parent / "evaluation_benchmark.json"
RESULTS_PATH = Path(__file__).resolve().parent / "eval_results.json"


def run_evaluation(top_k: int = 4) -> Dict[str, Any]:
    with open(BENCHMARK_PATH, "r", encoding="utf-8") as f:
        cases: List[Dict[str, Any]] = json.load(f)

    chain = SathyaRAGChain()

    factual_total = 0
    recall_hits = 0
    citation_hits = 0
    faithful_hits = 0

    redteam_total = 0
    redteam_passes = 0

    latencies: List[float] = []
    failures: List[Dict[str, Any]] = []

    for case in cases:
        res = chain.answer(case["query"], top_k=top_k)
        latencies.append(res["latency_ms"])
        ans_lower = res["answer"].lower()

        if case["expect_fallback"]:
            redteam_total += 1
            kw_ok = any(kw.lower() in ans_lower for kw in case["expected_keywords"])
            passed = bool(res["fallback_triggered"]) and kw_ok
            if passed:
                redteam_passes += 1
            else:
                failures.append({
                    "id": case["id"],
                    "category": case["category"],
                    "query": case["query"],
                    "reason": f"Expected fallback={case['expect_fallback']}, got {res['fallback_triggered']} ({res['guardrail_reason']})",
                    "answer_preview": res["answer"][:200],
                })
        else:
            factual_total += 1
            retrieved_docs = {
                ch.get("metadata", {}).get("document_id", "")
                for ch in res["retrieved_chunks"]
            }
            # Recall@k: at least one expected_doc appears in retrieved_docs (substring match supports combined FAQ doc IDs)
            recall_ok = any(
                exp in rdoc for exp in case["expected_docs"] for rdoc in retrieved_docs
            )
            if recall_ok:
                recall_hits += 1

            # Citation accuracy: [Source: ...] present and matches expected_docs
            has_source_tag = bool(re.search(r"\[Source:\s*.+?\|.+?\]", res["answer"]))
            cited_docs = {c["document_id"] for c in res["citations"]}
            cite_ok = has_source_tag and any(
                exp in cdoc for exp in case["expected_docs"] for cdoc in cited_docs
            )
            if cite_ok:
                citation_hits += 1

            # Faithfulness / factual keyword match across answer OR top retrieved context
            kw_ok = all(
                any(alt.lower() in ans_lower for alt in kw.split("|"))
                for kw in case["expected_keywords"]
            )
            faithful_ok = (not res["fallback_triggered"]) and kw_ok
            if faithful_ok:
                faithful_hits += 1

            if not (recall_ok and cite_ok and faithful_ok):
                failures.append({
                    "id": case["id"],
                    "category": case["category"],
                    "query": case["query"],
                    "recall_ok": recall_ok,
                    "cite_ok": cite_ok,
                    "faithful_ok": faithful_ok,
                    "expected_keywords": case["expected_keywords"],
                    "retrieved_docs": list(retrieved_docs),
                    "answer_preview": res["answer"][:250],
                })

    total = len(cases)
    overall_passes = faithful_hits + redteam_passes
    latencies_sorted = sorted(latencies)
    p95_idx = min(len(latencies_sorted) - 1, int(len(latencies_sorted) * 0.95))

    summary = {
        "total_cases": total,
        "factual_cases": factual_total,
        "redteam_cases": redteam_total,
        "retrieval_recall_at_k": round((recall_hits / factual_total) * 100, 2) if factual_total else 0.0,
        "faithfulness_accuracy": round((faithful_hits / factual_total) * 100, 2) if factual_total else 0.0,
        "citation_accuracy": round((citation_hits / factual_total) * 100, 2) if factual_total else 0.0,
        "guardrail_pass_rate": round((redteam_passes / redteam_total) * 100, 2) if redteam_total else 0.0,
        "overall_accuracy": round((overall_passes / total) * 100, 2) if total else 0.0,
        "mean_latency_ms": round(sum(latencies) / len(latencies), 2) if latencies else 0.0,
        "p95_latency_ms": round(latencies_sorted[p95_idx], 2) if latencies_sorted else 0.0,
        "failures_count": len(failures),
        "failures": failures,
    }

    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print("=== Sathya Assist Evaluation Report (Rahul) ===")
    print(f"Total Cases           : {summary['total_cases']} ({factual_total} factual, {redteam_total} red-team)")
    print(f"Retrieval Recall@{top_k}   : {summary['retrieval_recall_at_k']}%")
    print(f"Faithfulness Accuracy : {summary['faithfulness_accuracy']}%")
    print(f"Citation Accuracy     : {summary['citation_accuracy']}%")
    print(f"Guardrail Pass Rate   : {summary['guardrail_pass_rate']}%")
    print(f"Overall Accuracy      : {summary['overall_accuracy']}%")
    print(f"Latency (Mean / P95)  : {summary['mean_latency_ms']}ms / {summary['p95_latency_ms']}ms")
    print(f"Failures              : {summary['failures_count']}")
    for fail in failures:
        print(f"  [FAIL] {fail['id']} ({fail['category']}): {fail['query']}")
        print(f"         -> {fail.get('reason') or fail}")

    return summary


if __name__ == "__main__":
    run_evaluation()
