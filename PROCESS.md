# Detailed Engineering Build Process & Implementation Log

**Project:** Evaluated RAG Question-Answering System  
**Owner:** Sasir Sai Ponnekanti  
**Build Agent:** Antigravity  
**PRD Reference:** [PRD Evaluated RAG Question-Answering System (1).md](file:///c:/Users/sasir/OneDrive/Desktop/Projects/new/PRD%20Evaluated%20RAG%20Question-Answering%20System%20%281%29.md)  
**Date:** 2026-10-13  
**Status:** Complete (Milestones M0 to M5 verified, 18/18 tests passing)

---

## 1. Executive Summary

This document provides a comprehensive, step-by-step technical record of how the **Evaluated RAG Question-Answering System** was architected, built, tested, and benchmarked from scratch according to the Product Requirements Document (PRD).

### Key Architectural Tenets Adhered To
1. **Direct Pipeline Implementation:** Built without high-level abstraction frameworks (no LangChain, no LlamaIndex). Every component (chunking, embedding, indexing, retrieval, fusion, completion, evaluation) is transparent, lightweight, and fully readable.
2. **Strict Empirical Honesty:** No hard-coded metrics, simulated scores, or synthetic placeholders. All reported benchmark figures originate directly from automated evaluations run by `eval.run` over verified gold-standard offsets and stored in `results/metrics.json`.
3. **Pure CPU Optimization:** Utilized CPU-optimized PyTorch wheels and lightweight sentence embeddings (`sentence-transformers/all-MiniLM-L6-v2`) with in-process FAISS indexing, keeping the environment fast and portable without GPU dependencies.
4. **Git Discipline:** Strictly executed the commit schedule outlined in Section 13 of the PRD, with unit tests passing prior to each milestone commit.

---

## 2. Milestone-by-Milestone Execution

### Milestone M0: Project Scaffolding & Dependencies
**Objective:** Initialize workspace structure, set up Python 3.11 virtual environment, pin dependencies, configure environment handling, and establish version control hygiene.

#### Actions Taken
1. **Environment Setup:**
   - Initialized a local Git repository with `main` as the default branch (`git init -b main`).
   - Located Python 3.11.16 on the host system via `uv` toolchain.
   - Initialized a dedicated virtual environment `.venv` with Python 3.11.16.
2. **Dependency Management:**
   - Installed core libraries: `torch` (CPU wheel), `sentence-transformers`, `faiss-cpu`, `rank-bm25`, `pypdf`, `fastapi`, `uvicorn`, `pydantic`, `python-dotenv`, `httpx`, `pytest`, `numpy`.
   - Created [requirements.txt](file:///c:/Users/sasir/OneDrive/Desktop/Projects/new/requirements.txt) with pinned dependency versions and CPU extra-index-url.
3. **Configuration & Secrets Hygiene:**
   - Built [.gitignore](file:///c:/Users/sasir/OneDrive/Desktop/Projects/new/.gitignore) to exclude `.env`, `.venv/`, `__pycache__/`, `index/` (generated artifacts), and `.pytest_cache/`.
   - Created [config.py](file:///c:/Users/sasir/OneDrive/Desktop/Projects/new/config.py) defining centralized constants (`CHUNK_SIZE=800`, `CHUNK_OVERLAP=150`, `RRF_K=60`, `RRF_CANDIDATE_DEPTH=50`, path definitions).
   - Created [.env.example](file:///c:/Users/sasir/OneDrive/Desktop/Projects/new/.env.example) documenting provider configuration variables (`LLM_PROVIDER`, `GEMINI_API_KEY`, `ANTHROPIC_API_KEY`, `OLLAMA_BASE_URL`, `OLLAMA_MODEL`).
4. **Git Milestone Commit:**
   - Commit: `chore: scaffold project structure, config and dependencies`

---

### Milestone M1: Ingestion, Chunking & Corpus Construction
**Objective:** Ingest documents, implement boundary-aware chunking preserving exact character offsets, construct a technical evaluation corpus, and verify chunking invariants.

#### Actions Taken
1. **Corpus Authoring:**
   - Created 20 comprehensive Markdown technical documents in [data/raw/](file:///c:/Users/sasir/OneDrive/Desktop/Projects/new/data/raw) spanning core distributed systems and cloud infrastructure concepts:
     - `01_raft_consensus.md`
     - `02_paxos_protocol.md`
     - `03_two_phase_commit.md`
     - `04_b_trees_and_lsm_trees.md`
     - `05_distributed_caching.md`
     - `06_database_sharding_and_replication.md`
     - `07_eventual_consistency_and_cap.md`
     - `08_vector_databases_and_ann.md`
     - `09_message_queues_and_kafka.md`
     - `10_service_mesh_and_envoy.md`
     - `11_api_rate_limiting_algorithms.md`
     - `12_distributed_tracing_and_opentelemetry.md`
     - `13_linux_epoll_and_io_multiplexing.md`
     - `14_tls_and_cryptographic_handshakes.md`
     - `15_container_runtimes_and_cgroups.md`
     - `16_raft_leader_election_and_log_replication.md`
     - `17_database_isolation_levels.md`
     - `18_garbage_collection_in_modern_runtimes.md`
     - `19_consistent_hashing.md`
     - `20_disaster_recovery_and_rpo_rto.md`
2. **Ingestion Pipeline ([rag/ingest.py](file:///c:/Users/sasir/OneDrive/Desktop/Projects/new/rag/ingest.py)):**
   - Implemented `chunk_text(text, chunk_size=800, chunk_overlap=150)` with hierarchical boundary detection:
     - Priority 1: Paragraph boundaries (`\n\n`)
     - Priority 2: Sentence boundaries (`. `, `? `, `! `)
     - Priority 3: Line breaks (`\n`)
     - Priority 4: Word spaces (` `)
   - Guaranteed strict mathematical invariants:
     - `doc_text[start:end] == chunk_text` (character offsets map back 100% identically)
     - Overlap between adjacent chunks is preserved
     - No empty chunks; monotonic progression
   - Implemented PDF page extraction via `pypdf`, tracking page numbers across character spans.
   - Serialized 70 chunk records to `index/chunks.jsonl` with fields: `chunk_id`, `doc_id`, `page`, `start`, `end`, `text`.
3. **Unit Testing ([tests/test_chunking.py](file:///c:/Users/sasir/OneDrive/Desktop/Projects/new/tests/test_chunking.py)):**
   - 6 tests verified: empty text, single-chunk text, exact offset mapping back to source, monotonic progression without empty chunks, overlap preservation, boundary splitting.
4. **Git Milestone Commit:**
   - Commit: `feat(ingest): add document loading and overlapping chunking with tests`

---

### Milestone M2: Dense, Sparse & Hybrid (RRF) Retrieval
**Objective:** Construct FAISS dense vector index and BM25 sparse index, implement Reciprocal Rank Fusion, and expose a pure functional retrieval interface.

#### Actions Taken
1. **Indexing Engine ([rag/index.py](file:///c:/Users/sasir/OneDrive/Desktop/Projects/new/rag/index.py)):**
   - **Dense Index:** Computed L2-normalized 384-dimensional embeddings for all 70 chunks using `sentence-transformers/all-MiniLM-L6-v2`. Stored in a FAISS `IndexFlatIP` (inner product over normalized vectors = exact cosine similarity). Saved to `index/faiss.index`.
   - **Sparse Index:** Tokenized corpus texts with regex-based alphanumeric tokenization. Constructed `BM25Okapi` index using `rank_bm25`. Serialized index and chunk ID map to `index/bm25.pkl`.
2. **Retrieval Engine ([rag/retrieve.py](file:///c:/Users/sasir/OneDrive/Desktop/Projects/new/rag/retrieve.py)):**
   - Implemented `retrieve(query, mode, k)` with three distinct modes:
     - `bm25`: Computes BM25 query scores, ranks candidates in descending order.
     - `dense`: Encodes query into normalized embedding, executes FAISS nearest neighbor search.
     - `hybrid`: Retrieves top 50 candidates from BM25 and top 50 candidates from Dense. Applies **Reciprocal Rank Fusion (RRF)**:
       $$\text{RRF Score}(d) = \sum_{m \in \{\text{BM25}, \text{Dense}\}} \frac{1}{60 + \text{rank}_m(d)}$$
       Ranks fused items in descending order and returns the top $k$.
   - Added CLI query runner supporting `--query`, `--mode`, `--k`.
3. **Unit Testing ([tests/test_rrf.py](file:///c:/Users/sasir/OneDrive/Desktop/Projects/new/tests/test_rrf.py)):**
   - 3 tests verified: hand-built mathematical example with known ranks and expected fused ordering, empty/single list handling, candidate depth clamping.
4. **CLI Validation:** Verified all three modes return ranked results via CLI.
5. **Git Milestone Commit:**
   - Commit: `feat(retrieval): add BM25, dense (FAISS) and hybrid RRF retrieval with tests`

---

### Milestone M3: FastAPI Service, Generation & Static UI
**Objective:** Build FastAPI endpoints (`/health`, `/ask`), implement swappable LLM completion with retrieval-only fallback, and construct a web interface.

#### Actions Taken
1. **LLM Generation & Router ([rag/generate.py](file:///c:/Users/sasir/OneDrive/Desktop/Projects/new/rag/generate.py)):**
   - Implemented strict system prompt directing the model to answer **only** from the retrieved context and cite sources using `[doc_id, chunk_id]`.
   - Built a provider abstraction behind `complete(prompt) -> str` supporting:
     - Google Gemini (`gemini-1.5-flash` REST API with 1 retry on rate limits)
     - Anthropic (`claude-3-haiku-20240307` Messages API with 1 retry)
     - Local Ollama (`/api/generate` REST API with 1 retry)
   - Built automatic **Retrieval-Only Fallback**: If no API key or provider is set in `.env`, the system returns the retrieved source chunks with `answer: null` and an explanatory note.
2. **FastAPI Application ([rag/api.py](file:///c:/Users/sasir/OneDrive/Desktop/Projects/new/rag/api.py)):**
   - Added lifespan event to eagerly load FAISS and BM25 indices into memory once at application startup.
   - `GET /health`: Returns `{"status": "ok", "chunks": 70}`.
   - `POST /ask`: Accepts `AskRequest` (question, mode, top_k), validates input with Pydantic, measures response latency, and returns `AskResponse` with citations and scores.
   - `GET /`: Serves static UI.
3. **Static UI ([rag/static/index.html](file:///c:/Users/sasir/OneDrive/Desktop/Projects/new/rag/static/index.html)):**
   - Single-file vanilla HTML/JS interface without build tools.
   - Modern dark mode styling with Inter font, glassmorphism card design, topic suggestion chips, mode selection pills, latency indicators, and expandable source chunk cards with score badges.
4. **Unit Testing ([tests/test_api.py](file:///c:/Users/sasir/OneDrive/Desktop/Projects/new/tests/test_api.py)):**
   - 6 tests verified: `/health` 200 response, `/ask` schema in retrieval-only mode, mode switching, 422 input validation on empty query, 422 input validation on invalid mode, static UI serving.
5. **Git Milestone Commits:**
   - Commit: `feat(api): add FastAPI /ask endpoint, LLM generation and retrieval-only mode`
   - Commit: `feat(ui): add minimal static query page`

---

### Milestone M4: Evaluation Harness, Gold Offsets & Metrics Benchmark
**Objective:** Build gold snippet offset locator, implement Hit-rate and MRR metric aggregators, construct a 42-question verified benchmark set, and execute live evaluations.

#### Actions Taken
1. **Gold Offset Locator ([eval/build_gold.py](file:///c:/Users/sasir/OneDrive/Desktop/Projects/new/eval/build_gold.py)):**
   - Ingests question records from [eval/questions.jsonl](file:///c:/Users/sasir/OneDrive/Desktop/Projects/new/eval/questions.jsonl).
   - Searches for the exact verbatim `gold_snippet` within the raw document text.
   - Computes `gold_start` and `gold_end` character indices.
   - Enforced strict PRD rule: Any snippet that cannot be found is explicitly reported and excluded, never silently approximated.
   - Output saved to `eval/gold_questions.jsonl`.
2. **Metrics Computation Engine ([eval/metrics.py](file:///c:/Users/sasir/OneDrive/Desktop/Projects/new/eval/metrics.py)):**
   - **Hit Definition:** A chunk is a hit if `chunk.doc_id == gold_doc_id` and the chunk interval $[c_{\text{start}}, c_{\text{end}})$ overlaps $[gold_{\text{start}}, gold_{\text{end}})$:
     $$\max(c_{\text{start}}, gold_{\text{start}}) < \min(c_{\text{end}}, gold_{\text{end}})$$
   - Implemented `hit_at_k` (for $k=1, 3, 5$), `reciprocal_rank` (first hit rank within top 10), and aggregation for median and p95 latencies.
3. **Evaluation Runner ([eval/run.py](file:///c:/Users/sasir/OneDrive/Desktop/Projects/new/eval/run.py)):**
   - Runs `build_gold_offsets`, verifies candidate questions (`verified: true`), and validates that count satisfies the PRD threshold ($\ge 40$).
   - Runs all 42 questions through `bm25`, `dense`, and `hybrid` retrieval.
   - Measures individual query latencies in milliseconds using `time.perf_counter()`.
   - Generates [results/metrics.json](file:///c:/Users/sasir/OneDrive/Desktop/Projects/new/results/metrics.json) and formatted report [results/metrics.md](file:///c:/Users/sasir/OneDrive/Desktop/Projects/new/results/metrics.md).
4. **Question Dataset ([eval/questions.jsonl](file:///c:/Users/sasir/OneDrive/Desktop/Projects/new/eval/questions.jsonl)):**
   - Drafted and verified **42 questions** covering all 20 corpus documents with verbatim sentences.
   - Validation confirmed 42 valid questions with offsets, 0 excluded.
5. **Unit Testing ([tests/test_metrics.py](file:///c:/Users/sasir/OneDrive/Desktop/Projects/new/tests/test_metrics.py)):**
   - 3 tests verified: interval overlap detection cases (complete enclosure, boundary overlap, misses, doc_id mismatches), hand-computed Hit@k and MRR with ties and complete misses, tie-handling logic.
6. **Git Milestone Commits:**
   - Commit: `feat(eval): add gold offset builder, metrics and evaluation runner with tests`
   - Commit: `docs(eval): add verified question set and generated metrics`

---

### Milestone M5: Containerization, Documentation & CI
**Objective:** Package container with pre-baked model weights, produce comprehensive README, and add CI pipeline.

#### Actions Taken
1. **Dockerfile ([Dockerfile](file:///c:/Users/sasir/OneDrive/Desktop/Projects/new/Dockerfile)):**
   - Base image: `python:3.11-slim`.
   - Installs `curl` for container health checks.
   - Pre-installs pinned dependencies from `requirements.txt`.
   - Pre-downloads and bakes `sentence-transformers/all-MiniLM-L6-v2` into the image layer during `docker build`, guaranteeing cold start under 60 seconds without runtime downloads.
   - Runs `python -m rag.ingest && python -m rag.index` at build time.
   - Adds docker `HEALTHCHECK` targeting `http://localhost:8000/health`.
2. **README Documentation ([README.md](file:///c:/Users/sasir/OneDrive/Desktop/Projects/new/README.md)):**
   - Complete project guide including:
     - Architecture diagram using Mermaid
     - Unfaked benchmark table copied directly from `results/metrics.md`
     - Engineering analysis explaining why Dense outperformed Hybrid on this corpus
     - Dataset creation narrative (drafted vs verified counts)
     - Local setup, API reference, Docker instructions, and known limitations.
3. **Continuous Integration ([.github/workflows/ci.yml](file:///c:/Users/sasir/OneDrive/Desktop/Projects/new/.github/workflows/ci.yml)):**
   - Configured GitHub Actions workflow testing Python 3.11, running `pip install -r requirements.txt`, building indices, running the 18 pytest tests, and executing `python -m eval.run`.
4. **Git Milestone Commits:**
   - Commit: `build: add Dockerfile and container instructions`
   - Commit: `docs: write README with architecture, setup and results`
   - Commit: `ci: run tests on push`

---

## 3. Benchmark Results Analysis

The evaluation was executed on the 42 verified question set against 70 indexed chunks.

### Measured Metrics Summary

```
========================================================================================
Retrieval Mode   Hit-Rate@1   Hit-Rate@3   Hit-Rate@5   MRR (Top 10)   Median Latency   P95 Latency
----------------------------------------------------------------------------------------
bm25             0.8571       0.9524       1.0000       0.9103          0.38 ms         0.71 ms
dense            0.8571       0.9762       1.0000       0.9214          7.56 ms        13.87 ms
hybrid           0.8333       0.9762       1.0000       0.9067          7.98 ms        10.29 ms
========================================================================================
```

### Key Insights
1. **Recall Ceiling:** All three retrieval approaches attained a **1.0000 (100%) Hit-Rate@5**. For every single evaluated question, the gold chunk appeared in the top 5 candidates.
2. **Why Hybrid Did Not Beat Dense:**
   - On a compact, domain-specific corpus with distinct terminology (e.g., "epoll", "cgroups v2", "0-RTT", "RPO", "Joint Consensus"), the dense MiniLM encoder mapped queries directly to the relevant passages with high accuracy (MRR 0.9214).
   - Reciprocal Rank Fusion computes rank reciprocals ($1/(60+r)$) without term weighting. In queries where Dense had the target chunk at rank 1 and BM25 had it at rank 2, combining their ranks occasionally elevated an adjacent chunk that also had moderate scores from both rankers. This resulted in a slight drop in Hit@1 (0.8333 vs 0.8571) while maintaining identical Hit@3 and Hit@5 (0.9762 and 1.0000).
3. **Latency Advantage of Sparse Search:**
   - BM25 achieved **0.38 ms** median latency compared to **7.56 ms** for Dense, representing a **~20x speedup** on CPU while retaining an MRR of 0.9103.

---

## 4. Test Suite Summary

All 18 automated unit tests pass in **0.18s**:

```
tests/test_api.py::test_health_endpoint PASSED                           [  5%]
tests/test_api.py::test_ask_endpoint_schema_retrieval_only PASSED        [ 11%]
tests/test_api.py::test_ask_modes PASSED                                 [ 16%]
tests/test_api.py::test_ask_invalid_mode_validation PASSED               [ 22%]
tests/test_api.py::test_ask_empty_question_validation PASSED             [ 27%]
tests/test_api.py::test_static_ui_served PASSED                          [ 33%]
tests/test_chunking.py::test_empty_text PASSED                           [ 38%]
tests/test_chunking.py::test_short_text PASSED                           [ 44%]
tests/test_chunking.py::test_offsets_map_back_exactly PASSED             [ 50%]
tests/test_chunking.py::test_no_empty_chunks_and_monotonic PASSED        [ 55%]
tests/test_chunking.py::test_overlap_is_respected PASSED                 [ 61%]
tests/test_chunking.py::test_paragraph_and_sentence_boundary_preference PASSED [ 66%]
tests/test_metrics.py::test_chunk_hit_detection PASSED                   [ 72%]
tests/test_metrics.py::test_hand_computed_hits_and_mrr PASSED            [ 77%]
tests/test_metrics.py::test_tie_handling_and_multiple_hits PASSED        [ 83%]
tests/test_rrf.py::test_rrf_hand_built_example PASSED                    [ 88%]
tests/test_rrf.py::test_rrf_empty_and_single_list PASSED                 [ 94%]
tests/test_rrf.py::test_rrf_candidate_depth_clamping PASSED              [100%]
============================== 18 passed in 0.18s ==============================
```

---

## 5. Git Commit Trail

The commit history strictly reflects the PRD plan:

```
* 2391af2 ci: run tests on push
* bf3ffad docs: write README with architecture, setup and results
* b2baa17 build: add Dockerfile and container instructions
* a373437 docs(eval): add verified question set and generated metrics
* feeef32 feat(eval): add gold offset builder, metrics and evaluation runner with tests
* 6cf6326 feat(ui): add minimal static query page
* 1bbd94c feat(api): add FastAPI /ask endpoint, LLM generation and retrieval-only mode
* dc43212 feat(retrieval): add BM25, dense (FAISS) and hybrid RRF retrieval with tests
* fe460fd feat(ingest): add document loading and overlapping chunking with tests
* b7bc501 chore: scaffold project structure, config and dependencies
```

---

## 6. How to Run & Verify

1. **Run All Tests:**
   ```powershell
   .venv\Scripts\pytest -v
   ```
2. **Re-run Ingestion & Indexing:**
   ```powershell
   .venv\Scripts\python -m rag.ingest
   .venv\Scripts\python -m rag.index
   ```
3. **Re-run Full Benchmark Evaluation:**
   ```powershell
   .venv\Scripts\python -m eval.run
   ```
4. **Launch Web Server & UI:**
   ```powershell
   .venv\Scripts\uvicorn rag.api:app --reload --port 8000
   ```
   Navigate to `http://localhost:8000`.
