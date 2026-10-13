"""Retrieval engine supporting BM25, Dense (FAISS), and Hybrid (RRF) search."""

import argparse
import pickle
from typing import Any, Dict, List, Optional, Tuple
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

import config
from rag.index import load_chunks, tokenize


def compute_rrf_scores(
    ranked_lists: List[List[str]],
    k_rrf: int = config.RRF_K,
    candidate_depth: int = config.RRF_CANDIDATE_DEPTH,
) -> Dict[str, float]:
    """Computes Reciprocal Rank Fusion (RRF) scores over multiple ranked ID lists.

    Formula: score = sum(1 / (k_rrf + rank)), where rank is 1-based (1, 2, ...).
    Pure function with no side effects.
    """
    scores: Dict[str, float] = {}
    for r_list in ranked_lists:
        for rank, item_id in enumerate(r_list[:candidate_depth], start=1):
            scores[item_id] = scores.get(item_id, 0.0) + (1.0 / (k_rrf + rank))
    return scores


def fuse_ranked_lists(
    ranked_lists: List[List[str]],
    k_rrf: int = config.RRF_K,
    candidate_depth: int = config.RRF_CANDIDATE_DEPTH,
    top_k: int = config.DEFAULT_TOP_K,
) -> List[Tuple[str, float]]:
    """Fuses ranked ID lists using RRF and returns sorted (item_id, score) pairs."""
    scores = compute_rrf_scores(ranked_lists, k_rrf=k_rrf, candidate_depth=candidate_depth)
    # Sort descending by score; tie-break deterministically by item_id
    sorted_items = sorted(scores.items(), key=lambda x: (-x[1], x[0]))
    return sorted_items[:top_k]


class Retriever:
    """Retriever loading chunks and indices into memory for fast queries."""

    def __init__(
        self,
        chunks_path=config.CHUNKS_PATH,
        faiss_path=config.FAISS_INDEX_PATH,
        bm25_path=config.BM25_INDEX_PATH,
        model_name: str = config.EMBEDDING_MODEL_NAME,
    ):
        self.chunks: List[Dict[str, Any]] = load_chunks(chunks_path)
        self.chunk_by_id: Dict[str, Dict[str, Any]] = {c["chunk_id"]: c for c in self.chunks}

        # Load FAISS index
        self.faiss_index = faiss.read_index(str(faiss_path))
        self.embedding_model = SentenceTransformer(model_name)

        # Load BM25 index
        with open(bm25_path, "rb") as f:
            bm25_data = pickle.load(f)
            self.bm25 = bm25_data["bm25"]
            self.bm25_chunk_ids: List[str] = bm25_data["chunk_ids"]

    def retrieve_bm25(self, query: str, top_k: int = 50) -> List[Tuple[Dict[str, Any], float]]:
        """BM25 search returning (chunk, score)."""
        tokens = tokenize(query)
        if not tokens:
            return []
        scores = self.bm25.get_scores(tokens)
        top_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        for idx in top_indices:
            score = float(scores[idx])
            chunk_id = self.bm25_chunk_ids[idx]
            results.append((self.chunk_by_id[chunk_id], score))
        return results

    def retrieve_dense(self, query: str, top_k: int = 50) -> List[Tuple[Dict[str, Any], float]]:
        """FAISS dense cosine similarity search returning (chunk, score)."""
        query_emb = self.embedding_model.encode(
            [query], show_progress_bar=False, normalize_embeddings=True
        )
        query_emb = np.ascontiguousarray(query_emb, dtype=np.float32)

        search_k = min(top_k, self.faiss_index.ntotal)
        scores, indices = self.faiss_index.search(query_emb, search_k)

        results = []
        for idx, score in zip(indices[0], scores[0]):
            if idx < 0 or idx >= len(self.chunks):
                continue
            chunk = self.chunks[idx]
            results.append((chunk, float(score)))
        return results

    def retrieve_hybrid(
        self,
        query: str,
        top_k: int = config.DEFAULT_TOP_K,
        candidate_depth: int = config.RRF_CANDIDATE_DEPTH,
        k_rrf: int = config.RRF_K,
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Hybrid search combining BM25 and Dense with Reciprocal Rank Fusion."""
        bm25_results = self.retrieve_bm25(query, top_k=candidate_depth)
        dense_results = self.retrieve_dense(query, top_k=candidate_depth)

        bm25_ids = [c["chunk_id"] for c, _ in bm25_results]
        dense_ids = [c["chunk_id"] for c, _ in dense_results]

        fused = fuse_ranked_lists([bm25_ids, dense_ids], k_rrf=k_rrf, candidate_depth=candidate_depth, top_k=top_k)

        results = []
        for chunk_id, score in fused:
            results.append((self.chunk_by_id[chunk_id], score))
        return results

    def retrieve(
        self,
        query: str,
        mode: str = "hybrid",
        k: int = config.DEFAULT_TOP_K,
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Retrieves top k chunks for query under specified mode ('bm25', 'dense', 'hybrid')."""
        mode = mode.lower().strip()
        if mode == "bm25":
            return self.retrieve_bm25(query, top_k=k)
        elif mode == "dense":
            return self.retrieve_dense(query, top_k=k)
        elif mode == "hybrid":
            return self.retrieve_hybrid(query, top_k=k)
        else:
            raise ValueError(f"Unknown retrieval mode: '{mode}'. Must be 'bm25', 'dense', or 'hybrid'.")


_GLOBAL_RETRIEVER: Optional[Retriever] = None


def get_retriever() -> Retriever:
    """Returns singleton retriever instance."""
    global _GLOBAL_RETRIEVER
    if _GLOBAL_RETRIEVER is None:
        _GLOBAL_RETRIEVER = Retriever()
    return _GLOBAL_RETRIEVER


def retrieve(
    query: str,
    mode: str = "hybrid",
    k: int = config.DEFAULT_TOP_K,
) -> List[Tuple[Dict[str, Any], float]]:
    """Functional retrieval entry point."""
    retriever = get_retriever()
    return retriever.retrieve(query=query, mode=mode, k=k)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Query the RAG retrieval engine.")
    parser.add_argument("--query", type=str, required=True, help="Search query")
    parser.add_argument("--mode", type=str, default="hybrid", choices=["bm25", "dense", "hybrid"])
    parser.add_argument("--k", type=int, default=5, help="Number of chunks to return")
    args = parser.parse_args()

    results = retrieve(args.query, mode=args.mode, k=args.k)
    print(f"\n--- Retrieved {len(results)} results (mode={args.mode}) for query: '{args.query}' ---")
    for rank, (chunk, score) in enumerate(results, start=1):
        print(f"#{rank} [Score: {score:.5f}] {chunk['doc_id']} ({chunk['chunk_id']})")
        print(f"    {chunk['text'][:140].strip()}...\n")
