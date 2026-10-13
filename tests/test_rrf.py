"""Tests for Reciprocal Rank Fusion (RRF) logic in rag/retrieve.py."""

import pytest
from rag.retrieve import compute_rrf_scores, fuse_ranked_lists


def test_rrf_hand_built_example():
    """Hand-built example with known ranks verifying exact score calculation and fused order."""
    list1 = ["item_a", "item_b", "item_c"]
    list2 = ["item_b", "item_d", "item_a"]

    k_rrf = 60
    scores = compute_rrf_scores([list1, list2], k_rrf=k_rrf, candidate_depth=50)

    # Exact expected scores
    expected_score_b = (1.0 / (60 + 2)) + (1.0 / (60 + 1))  # 1/62 + 1/61
    expected_score_a = (1.0 / (60 + 1)) + (1.0 / (60 + 3))  # 1/61 + 1/63
    expected_score_d = 1.0 / (60 + 2)                        # 1/62
    expected_score_c = 1.0 / (60 + 3)                        # 1/63

    assert pytest.approx(scores["item_b"], rel=1e-5) == expected_score_b
    assert pytest.approx(scores["item_a"], rel=1e-5) == expected_score_a
    assert pytest.approx(scores["item_d"], rel=1e-5) == expected_score_d
    assert pytest.approx(scores["item_c"], rel=1e-5) == expected_score_c

    # Fused order: B must be first, followed by A, then D, then C
    fused = fuse_ranked_lists([list1, list2], k_rrf=60, top_k=4)
    fused_ids = [item_id for item_id, _ in fused]
    assert fused_ids == ["item_b", "item_a", "item_d", "item_c"]


def test_rrf_empty_and_single_list():
    assert compute_rrf_scores([]) == {}

    single = ["doc1", "doc2"]
    fused = fuse_ranked_lists([single], k_rrf=60, top_k=2)
    assert len(fused) == 2
    assert fused[0][0] == "doc1"
    assert fused[1][0] == "doc2"
    assert pytest.approx(fused[0][1], rel=1e-5) == 1.0 / 61
    assert pytest.approx(fused[1][1], rel=1e-5) == 1.0 / 62


def test_rrf_candidate_depth_clamping():
    long_list = [f"doc_{i}" for i in range(100)]
    # With candidate_depth=10, docs beyond index 9 should not be scored
    scores = compute_rrf_scores([long_list], k_rrf=60, candidate_depth=10)
    assert len(scores) == 10
    assert "doc_0" in scores
    assert "doc_9" in scores
    assert "doc_10" not in scores
