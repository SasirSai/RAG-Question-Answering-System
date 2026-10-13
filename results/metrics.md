# Retrieval Strategy Evaluation Results


- **Timestamp:** `2026-10-13T09:56:08.461940+00:00`
- **Verified Questions Evaluated:** `42`
- **Indexed Chunks:** `70`
- **Embedding Model:** `sentence-transformers/all-MiniLM-L6-v2`
- **RRF Parameters:** `k=60`, `depth=50`

| Retrieval Mode | Hit-Rate@1 | Hit-Rate@3 | Hit-Rate@5 | MRR (Top 10) | Median Latency (ms) | P95 Latency (ms) |
| --- | --- | --- | --- | --- | --- | --- |
| `bm25` | 0.8571 | 0.9524 | 1.0000 | 0.9103 | 0.38 ms | 0.71 ms |
| `dense` | 0.8571 | 0.9762 | 1.0000 | 0.9214 | 7.56 ms | 13.87 ms |
| `hybrid` | 0.8333 | 0.9762 | 1.0000 | 0.9067 | 7.98 ms | 10.29 ms |
