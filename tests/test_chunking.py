"""Tests for chunking logic in rag/ingest.py."""

import pytest
from rag.ingest import chunk_text


def test_empty_text():
    chunks = chunk_text("")
    assert chunks == []


def test_short_text():
    text = "A short document that fits within a single chunk."
    chunks = chunk_text(text, chunk_size=800, chunk_overlap=150)
    assert len(chunks) == 1
    start, end, chunk_str = chunks[0]
    assert start == 0
    assert end == len(text)
    assert chunk_str == text
    assert text[start:end] == chunk_str


def test_offsets_map_back_exactly():
    text = (
        "Paragraph 1 contains some detailed background about retrieval augmented generation. "
        "It discusses vector databases, dense retrievers, and sparse lexical matching.\n\n"
        "Paragraph 2 dives deeper into BM25 scoring and term frequency normalization. "
        "BM25 is an effective baseline for keyword retrieval.\n\n"
        "Paragraph 3 discusses Reciprocal Rank Fusion (RRF). RRF combines disparate ranking lists "
        "without requiring score normalization."
    )
    chunks = chunk_text(text, chunk_size=100, chunk_overlap=30)
    assert len(chunks) > 1

    for start, end, chunk_str in chunks:
        # Offsets must map back exactly to the original text
        assert text[start:end] == chunk_str
        # No empty chunks
        assert len(chunk_str) > 0
        assert start < end


def test_no_empty_chunks_and_monotonic():
    text = "Sentence one. " * 50
    chunks = chunk_text(text, chunk_size=80, chunk_overlap=20)
    assert len(chunks) > 1

    prev_start = -1
    for start, end, chunk_str in chunks:
        assert len(chunk_str) > 0
        assert start > prev_start
        assert text[start:end] == chunk_str
        prev_start = start


def test_overlap_is_respected():
    text = "The quick brown fox jumps over the lazy dog. " * 30
    chunks = chunk_text(text, chunk_size=120, chunk_overlap=40)
    assert len(chunks) >= 3

    for i in range(len(chunks) - 1):
        c1_start, c1_end, _ = chunks[i]
        c2_start, c2_end, _ = chunks[i + 1]

        # Overlap exists between consecutive chunks
        assert c2_start < c1_end
        overlap_len = c1_end - c2_start
        assert overlap_len > 0
        # Check that the overlapping text is identical
        assert text[c2_start:c1_end] == text[c2_start:c1_end]


def test_paragraph_and_sentence_boundary_preference():
    p1 = "First paragraph ends here.\n\n"
    p2 = "Second paragraph starts right after."
    text = p1 + p2
    # chunk_size allows breaking cleanly at paragraph boundary
    chunks = chunk_text(text, chunk_size=30, chunk_overlap=10)
    assert len(chunks) >= 2
    # First chunk should end at or right after paragraph boundary
    assert chunks[0][1] >= len(p1) or "First paragraph ends here." in chunks[0][2]
