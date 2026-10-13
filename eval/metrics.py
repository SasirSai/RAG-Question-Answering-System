"""Metrics computation for evaluation harness: Hit-rate@k, MRR, and Latencies."""

from typing import Any, Dict, List, Optional
import numpy as np


def is_chunk_hit(chunk: Dict[str, Any], gold_doc_id: str, gold_start: int, gold_end: int) -> bool:
    """A retrieved chunk is a hit if it matches gold_doc_id and overlaps [gold_start, gold_end)."""
    if chunk.get("doc_id") != gold_doc_id:
        return False
    c_start = chunk.get("start", 0)
    c_end = chunk.get("end", 0)
    # Check interval overlap: max(start1, start2) < min(end1, end2)
    return max(c_start, gold_start) < min(c_end, gold_end)


def compute_hit_at_k(hits: List[bool], k: int) -> float:
    """Returns 1.0 if any hit exists in top k, else 0.0."""
    return 1.0 if any(hits[:k]) else 0.0


def compute_reciprocal_rank(hits: List[bool], top_n: int = 10) -> float:
    """Returns reciprocal rank (1/r) for the first hit within top_n, else 0.0."""
    for rank, hit in enumerate(hits[:top_n], start=1):
        if hit:
            return 1.0 / rank
    return 0.0


def evaluate_query_hits(
    retrieved_chunks: List[Dict[str, Any]],
    gold_doc_id: str,
    gold_start: int,
    gold_end: int,
) -> Dict[str, float]:
    """Evaluates hits and reciprocal rank for a single query."""
    hits = [is_chunk_hit(c, gold_doc_id, gold_start, gold_end) for c in retrieved_chunks]
    return {
        "hit_at_1": compute_hit_at_k(hits, 1),
        "hit_at_3": compute_hit_at_k(hits, 3),
        "hit_at_5": compute_hit_at_k(hits, 5),
        "reciprocal_rank": compute_reciprocal_rank(hits, 10),
    }


def aggregate_metrics(query_results: List[Dict[str, Any]], latencies_ms: List[float]) -> Dict[str, float]:
    """Aggregates per-query metrics into overall benchmark summary."""
    n = len(query_results)
    if n == 0:
        return {
            "hit_rate_at_1": 0.0,
            "hit_rate_at_3": 0.0,
            "hit_rate_at_5": 0.0,
            "mrr": 0.0,
            "median_latency_ms": 0.0,
            "p95_latency_ms": 0.0,
        }

    hit_1 = sum(r["hit_at_1"] for r in query_results) / n
    hit_3 = sum(r["hit_at_3"] for r in query_results) / n
    hit_5 = sum(r["hit_at_5"] for r in query_results) / n
    mrr = sum(r["reciprocal_rank"] for r in query_results) / n

    median_lat = float(np.median(latencies_ms)) if latencies_ms else 0.0
    p95_lat = float(np.percentile(latencies_ms, 95)) if latencies_ms else 0.0

    return {
        "hit_rate_at_1": round(hit_1, 4),
        "hit_rate_at_3": round(hit_3, 4),
        "hit_rate_at_5": round(hit_5, 4),
        "mrr": round(mrr, 4),
        "median_latency_ms": round(median_lat, 2),
        "p95_latency_ms": round(p95_lat, 2),
    }
