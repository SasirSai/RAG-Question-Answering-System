"""Index construction for dense (FAISS) and sparse (BM25) retrieval."""

import json
import pickle
import re
from pathlib import Path
from typing import Any, Dict, List
import faiss
import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

import config
from rag.ingest import ingest_corpus


def tokenize(text: str) -> List[str]:
    """Simple alphanumeric tokenizer for BM25."""
    return re.findall(r"\w+", text.lower())


def load_chunks(chunks_path: Path = config.CHUNKS_PATH) -> List[Dict[str, Any]]:
    """Loads chunk records from jsonl file."""
    if not chunks_path.exists():
        ingest_corpus()

    chunks: List[Dict[str, Any]] = []
    with open(chunks_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                chunks.append(json.loads(line))
    return chunks


def build_indices(
    chunks_path: Path = config.CHUNKS_PATH,
    faiss_path: Path = config.FAISS_INDEX_PATH,
    bm25_path: Path = config.BM25_INDEX_PATH,
    model_name: str = config.EMBEDDING_MODEL_NAME,
):
    """Builds and saves FAISS dense index and BM25 sparse index."""
    chunks = load_chunks(chunks_path)
    if not chunks:
        raise ValueError(f"No chunks found in {chunks_path}. Run ingestion first.")

    print(f"Building indices for {len(chunks)} chunks...")
    config.INDEX_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Dense Index (FAISS IndexFlatIP with normalized vectors)
    print(f"Loading embedding model: {model_name}...")
    model = SentenceTransformer(model_name)
    texts = [c["text"] for c in chunks]

    print("Computing embeddings...")
    embeddings = model.encode(texts, batch_size=32, show_progress_bar=False, normalize_embeddings=True)
    embeddings = np.ascontiguousarray(embeddings, dtype=np.float32)

    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)
    faiss.write_index(index, str(faiss_path))
    print(f"Dense index saved to {faiss_path} (dimension={dimension}, total={index.ntotal})")

    # 2. Sparse Index (BM25Okapi)
    print("Tokenizing texts for BM25...")
    tokenized_corpus = [tokenize(c["text"]) for c in chunks]
    bm25 = BM25Okapi(tokenized_corpus)

    bm25_data = {
        "bm25": bm25,
        "chunk_ids": [c["chunk_id"] for c in chunks],
    }
    with open(bm25_path, "wb") as f:
        pickle.dump(bm25_data, f)
    print(f"BM25 index saved to {bm25_path}")


if __name__ == "__main__":
    build_indices()
