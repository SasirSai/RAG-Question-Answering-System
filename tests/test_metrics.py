"""Unit tests for metrics calculation in eval/metrics.py."""

import pytest
from eval.metrics import (
    aggregate_metrics,
    compute_hit_at_k,
    compute_reciprocal_rank,
    evaluate_query_hits,
    is_chunk_hit,
)


def test_chunk_hit_detection():
    chunk = {"doc_id": "doc1.md", "start": 100, "end": 500}

    # Overlap case 1: chunk completely encloses gold
    assert is_chunk_hit(chunk, "doc1.md", 200, 300) is True

    # Overlap case 2: partial overlap at start
    assert is_chunk_hit(chunk, "doc1.md", 50, 150) is True

    # Overlap case 3: partial overlap at end
    assert is_chunk_hit(chunk, "doc1.md", 450, 600) is True

    # Miss case 1: completely before
    assert is_chunk_hit(chunk, "doc1.md", 0, 100) is False

    # Miss case 2: completely after
    assert is_chunk_hit(chunk, "doc1.md", 500, 600) is False

    # Miss case 3: wrong doc_id
    assert is_chunk_hit(chunk, "doc2.md", 200, 300) is False


def test_hand_computed_hits_and_mrr():
    """Hand-computed cases: hit at 1, hit at 2, hit at 4, and complete miss."""
    # Case 1: Hit at rank 1
    hits_c1 = [True, False, False, False, False]
    assert compute_hit_at_k(hits_c1, 1) == 1.0
    assert compute_hit_at_k(hits_c1, 3) == 1.0
    assert compute_hit_at_k(hits_c1, 5) == 1.0
    assert compute_reciprocal_rank(hits_c1) == 1.0

    # Case 2: Hit at rank 2
    hits_c2 = [False, True, False, False, False]
    assert compute_hit_at_k(hits_c2, 1) == 0.0
    assert compute_hit_at_k(hits_c2, 3) == 1.0
    assert compute_hit_at_k(hits_c2, 5) == 1.0
    assert compute_reciprocal_rank(hits_c2) == 0.5

    # Case 3: Hit at rank 4
    hits_c3 = [False, False, False, True, False]
    assert compute_hit_at_k(hits_c3, 1) == 0.0
    assert compute_hit_at_k(hits_c3, 3) == 0.0
    assert compute_hit_at_k(hits_c3, 5) == 1.0
    assert compute_reciprocal_rank(hits_c3) == 0.25

    # Case 4: Complete miss (no hits in top 10)
    hits_c4 = [False] * 10
    assert compute_hit_at_k(hits_c4, 1) == 0.0
    assert compute_hit_at_k(hits_c4, 3) == 0.0
    assert compute_hit_at_k(hits_c4, 5) == 0.0
    assert compute_reciprocal_rank(hits_c4) == 0.0

    # Aggregate over the 4 cases
    q_results = [
        {"hit_at_1": 1.0, "hit_at_3": 1.0, "hit_at_5": 1.0, "reciprocal_rank": 1.0},
        {"hit_at_1": 0.0, "hit_at_3": 1.0, "hit_at_5": 1.0, "reciprocal_rank": 0.5},
        {"hit_at_1": 0.0, "hit_at_3": 0.0, "hit_at_5": 1.0, "reciprocal_rank": 0.25},
        {"hit_at_1": 0.0, "hit_at_3": 0.0, "hit_at_5": 0.0, "reciprocal_rank": 0.0},
    ]
    latencies = [100.0, 150.0, 200.0, 250.0]

    agg = aggregate_metrics(q_results, latencies)
    assert agg["hit_rate_at_1"] == 0.25  # 1 / 4
    assert agg["hit_rate_at_3"] == 0.50  # 2 / 4
    assert agg["hit_rate_at_5"] == 0.75  # 3 / 4
    assert agg["mrr"] == 0.4375          # (1.0 + 0.5 + 0.25 + 0.0) / 4 = 1.75 / 4
    assert agg["median_latency_ms"] == 175.0
    assert agg["p95_latency_ms"] == pytest.approx(242.5, rel=1e-2)


def test_tie_handling_and_multiple_hits():
    """If multiple hits exist in the top 10, MRR uses the first (highest-ranked) hit."""
    hits_tie = [False, True, True, False]
    assert compute_reciprocal_rank(hits_tie) == 0.5  # First hit is at rank 2
