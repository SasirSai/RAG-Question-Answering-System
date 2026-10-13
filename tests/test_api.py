"""Tests for FastAPI endpoints in rag/api.py."""

import pytest
from fastapi.testclient import TestClient
from rag.api import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "chunks" in data
    assert isinstance(data["chunks"], int)
    assert data["chunks"] > 0


def test_ask_endpoint_schema_retrieval_only():
    payload = {
        "question": "What is the Raft Log Matching Property?",
        "mode": "hybrid",
        "top_k": 3,
    }
    response = client.post("/ask", json=payload)
    assert response.status_code == 200
    data = response.json()

    # Verify schema fields
    assert "answer" in data
    assert "sources" in data
    assert "mode" in data
    assert "latency_ms" in data

    assert data["mode"] == "hybrid"
    assert isinstance(data["latency_ms"], int)
    assert data["latency_ms"] >= 0

    assert isinstance(data["sources"], list)
    assert len(data["sources"]) <= 3
    if data["sources"]:
        s0 = data["sources"][0]
        assert "doc_id" in s0
        assert "chunk_id" in s0
        assert "score" in s0
        assert "text" in s0


def test_ask_modes():
    for mode in ["bm25", "dense", "hybrid"]:
        res = client.post("/ask", json={"question": "consistent hashing", "mode": mode, "top_k": 2})
        assert res.status_code == 200
        data = res.json()
        assert data["mode"] == mode
        assert len(data["sources"]) <= 2


def test_ask_invalid_mode_validation():
    response = client.post("/ask", json={"question": "hello", "mode": "invalid_mode"})
    assert response.status_code == 422


def test_ask_empty_question_validation():
    response = client.post("/ask", json={"question": ""})
    assert response.status_code == 422


def test_static_ui_served():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "Evaluated RAG QA Engine" in response.text
