"""FastAPI application for RAG Question-Answering system."""

import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

import config
from rag.generate import generate_answer
from rag.retrieve import get_retriever

STATIC_DIR = Path(__file__).resolve().parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Eagerly load retriever and indices once at startup
    retriever = get_retriever()
    print(f"Indices loaded at startup: {len(retriever.chunks)} chunks active.")
    yield


app = FastAPI(
    title="Evaluated RAG QA API",
    description="Question-answering API with BM25, dense FAISS, and hybrid RRF retrieval.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000, description="The user query or question.")
    mode: Literal["hybrid", "dense", "bm25"] = Field(
        default="hybrid", description="Retrieval mode: 'hybrid', 'dense', or 'bm25'."
    )
    top_k: int = Field(default=config.DEFAULT_TOP_K, ge=1, le=50, description="Number of source chunks to retrieve.")


class SourceItem(BaseModel):
    doc_id: str
    chunk_id: str
    page: Optional[int] = None
    score: float
    text: str


class AskResponse(BaseModel):
    answer: Optional[str] = None
    sources: List[SourceItem]
    mode: str
    latency_ms: int
    note: Optional[str] = None


@app.get("/health")
def health_check():
    """Health status and chunk count."""
    retriever = get_retriever()
    return {
        "status": "ok",
        "chunks": len(retriever.chunks),
    }


@app.post("/ask", response_model=AskResponse)
def ask_question(req: AskRequest):
    """Answers a question citing sources or returns retrieved sources in retrieval-only mode."""
    t0 = time.perf_counter()
    retriever = get_retriever()

    try:
        ranked_results = retriever.retrieve(query=req.question, mode=req.mode, k=req.top_k)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retrieval error: {str(e)}")

    chunks = [c for c, _ in ranked_results]
    answer, note = generate_answer(req.question, chunks)

    sources = [
        SourceItem(
            doc_id=c.get("doc_id", "unknown"),
            chunk_id=c.get("chunk_id", "unknown"),
            page=c.get("page"),
            score=round(score, 6),
            text=c.get("text", ""),
        )
        for c, score in ranked_results
    ]

    latency_ms = max(1, int((time.perf_counter() - t0) * 1000))

    return AskResponse(
        answer=answer,
        sources=sources,
        mode=req.mode,
        latency_ms=latency_ms,
        note=note,
    )


@app.get("/")
def serve_ui():
    """Serves the minimal static query interface."""
    index_html = STATIC_DIR / "index.html"
    if not index_html.exists():
        raise HTTPException(status_code=404, detail="Static UI index.html not found.")
    return FileResponse(str(index_html))
