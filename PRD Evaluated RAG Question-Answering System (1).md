# PRD: Evaluated RAG Question-Answering System

**Owner:** Sasir Sai Ponnekanti\
**Build agent:** Antigravity\
**Time budget:** 3 hours\
**Status:** Ready to build

---

## 0. Instructions to the build agent (read first)

You are building this project end to end. Follow these rules throughout:

1. **Work milestone by milestone** (Section 9). After each milestone, run the code and tests, and report what passed and what failed before continuing.
2. **Never fake results.** No hard-coded metrics, no placeholder numbers, no "expected" values in the README. Every number in the README must be written by the evaluation script into `results/metrics.json` and copied from there. If a step fails, say so plainly.
3. **Report results honestly even if hybrid retrieval does not beat dense retrieval.** The deliverable is the comparison, not a particular winner.
4. **CPU only.** No GPU assumptions. Keep every dependency installable with `pip` on a normal laptop.
5. **Pin dependency versions** in `requirements.txt` after confirming the install works.
6. **Keep the code small and readable.** The owner must be able to read and explain every file. Prefer simple functions over frameworks. Do not use LangChain or LlamaIndex; implement the pipeline directly.
7. **Ask the owner (stop and wait) only for the three human inputs in Section 3.** Make reasonable assumptions for everything else and note them in the README.
8. If a required secret (an API key) is missing, do not invent one: run in retrieval-only mode (Section 5.5) and say so.

---

## 1. Overview

A question-answering system over a custom document corpus using **retrieval-augmented generation (RAG)**. A user asks a question, the system retrieves the most relevant passages, and an LLM answers using only those passages, citing its sources.

What makes this project resume-worthy is **measurement**: a labelled question set, an evaluation harness, and a comparison of three retrieval strategies (BM25 only, dense embeddings only, hybrid), reported with real metrics.

## 2. Goals and non-goals

### Goals

- G1. Ingest PDFs, Markdown and text files from a folder into a searchable index.
- G2. Implement three retrieval modes: `bm25`, `dense`, `hybrid`.
- G3. Answer questions through a FastAPI endpoint, with citations to source chunks.
- G4. Evaluate all three modes on a labelled question set and write the results to a file.
- G5. Ship in a Docker container with a README that lets a stranger run it in under 10 minutes.

### Non-goals

- Authentication, user accounts, multi-tenancy.
- A hosted vector database server (use FAISS in-process).
- Model fine-tuning.
- Cloud deployment (optional stretch only).
- Chat memory across turns (single-turn Q&A only).

## 3. Human inputs required (the only things to stop and ask for)

| # | Input | Details |
| --- | --- | --- |
| H1 | **Corpus** | A folder of 15-40 documents (roughly 100-400 pages total) placed in `data/raw/`. Must be something the owner may legally use and, if publishing the repo, redistribute. If the corpus cannot be published, add `data/raw/` to `.gitignore` and say so in the README. |
| H2 | **LLM access** | One of: a Gemini API key, an Anthropic API key, or a local Ollama model name. Stored in `.env` (never committed). If none is provided, run retrieval-only mode. |
| H3 | **Verified evaluation labels** | The agent may draft candidate questions from corpus passages, but the owner must read and correct each one in `eval/questions.jsonl`. Only verified questions count toward reported metrics. State in the README how many were agent-drafted and human-verified. |

## 4. Users and use case

Primary user: the owner, demonstrating a working, measured RAG system to recruiters and interviewers. Secondary user: anyone cloning the repo to query the corpus.

## 5. Functional requirements

### 5.1 Ingestion (`rag/ingest.py`)

- Read `.pdf` (use `pypdf` or `pymupdf`), `.md` and `.txt` from `data/raw/`.
- Normalise whitespace; keep the original text so character offsets stay valid.
- Split into chunks of about **800 characters with 150 characters overlap**, breaking on paragraph or sentence boundaries where possible. Chunk size and overlap are configurable in `config.py`.
- Each chunk record: `chunk_id` (stable string), `doc_id` (file name), `page` (if available), `start` and `end` character offsets in the document text, and `text`.
- Persist chunks to `index/chunks.jsonl`.
- CLI: `python -m rag.ingest`. Must be idempotent (re-running rebuilds cleanly).

### 5.2 Indexing (`rag/index.py`)

- **Dense:** embed chunks with `sentence-transformers/all-MiniLM-L6-v2` (normalised vectors) and store in a FAISS `IndexFlatIP`. Save to `index/faiss.index`.
- **Sparse:** build a BM25 index over tokenised chunks with `rank_bm25` (`BM25Okapi`). Save with `pickle` (or rebuild at startup; note which).
- CLI: `python -m rag.index`.

### 5.3 Retrieval (`rag/retrieve.py`)

- `retrieve(query, mode, k)` returns a ranked list of `(chunk, score)`.
- Modes:
  - `bm25`: BM25 scores only.
  - `dense`: cosine similarity from FAISS.
  - `hybrid`: **Reciprocal Rank Fusion** over the top 50 from each ranker, `score = sum(1 / (60 + rank))`. Return the top `k`.
- Pure functions with no hidden global state, so they can be unit tested.

### 5.4 Generation (`rag/generate.py`)

- Build a prompt from the top-k chunks (default `k=5`).
- System instruction: answer **only** from the provided context; cite sources as `[doc_id, chunk_id]`; if the context does not contain the answer, reply that the documents do not contain it.
- The LLM provider is chosen by `LLM_PROVIDER` in `.env` (`gemini`, `anthropic`, or `ollama`). Keep the provider code behind one small function `complete(prompt) -> str` so providers are swappable.
- Temperature 0. Handle API errors and rate limits with a clear message and one retry.

### 5.5 Retrieval-only mode

If no LLM is configured, `/ask` returns the retrieved chunks with `answer: null` and a note. **The evaluation harness must work fully in this mode**, since retrieval metrics do not need an LLM.

### 5.6 API (`rag/api.py`, FastAPI)

- `GET /health` returns `{"status": "ok", "chunks": <int>}`.
- `POST /ask` with body `{"question": str, "mode": "hybrid"|"dense"|"bm25", "top_k": int}` (defaults `hybrid`, 5). Response:

```json
{
  "answer": "string or null",
  "sources": [{"doc_id": "...", "chunk_id": "...", "page": 3, "score": 0.031, "text": "..."}],
  "mode": "hybrid",
  "latency_ms": 412
}
```

- Validate input with Pydantic; return clear 4xx errors; load indices once at startup.
- Serve a minimal static page at `/` (one HTML file, plain JS, no build step) with a question box, a mode dropdown, the answer, and expandable source chunks.

### 5.7 Evaluation (`eval/`)

**Question file** `eval/questions.jsonl`, one JSON object per line:

```json
{"id": "q001", "question": "...", "gold_doc_id": "handbook.pdf", "gold_snippet": "verbatim sentence from the document that answers the question", "verified": true}
```

**Gold offsets:** `python -m eval.build_gold` locates each `gold_snippet` in its document text and records `gold_start` and `gold_end`. Any snippet that cannot be found must be reported and excluded, not silently fixed.

**Hit definition:** a retrieved chunk is a hit if it comes from `gold_doc_id` and its `[start, end)` range overlaps the gold range.

**Metrics** (computed for each mode, over `verified: true` questions only):

- hit-rate@1, @3, @5
- MRR (mean reciprocal rank, over the top 10)
- median and p95 retrieval latency in milliseconds

**Outputs:**

- `results/metrics.json` (machine-readable, includes question count, mode, every metric, timestamp, and the config used).
- `results/metrics.md` (a table generated from the JSON).
- `python -m eval.run` regenerates both. The README table is copied from `results/metrics.md` and never edited by hand.

**Minimum question count:** 40 verified questions. If fewer than 40 are verified, the report must print the actual count prominently.

**Optional generation check (stretch):** the owner manually spot-checks 10 answers for groundedness and records the count in the README, labelled as a manual check. No automated LLM-judge numbers unless the judge prompt is included in the repo.

## 6. Non-functional requirements

- Python 3.11. Dependencies installable on CPU, with the CPU build of PyTorch.
- Cold start under 60 seconds with the embedding model baked into the Docker image.
- Retrieval latency target: median under 200 ms on the evaluation corpus (report the actual figure, whatever it is).
- Secrets only in `.env`; commit `.env.example`.
- Reproducible: a fixed random seed wherever randomness is used; the config snapshot is stored in the metrics file.

## 7. Repository structure

```
rag-qa/
  README.md
  requirements.txt
  Dockerfile
  .env.example
  .gitignore
  config.py
  data/raw/            # corpus (human input H1)
  index/               # generated: chunks.jsonl, faiss.index, bm25.pkl
  rag/
    __init__.py
    ingest.py
    index.py
    retrieve.py
    generate.py
    api.py
    static/index.html
  eval/
    questions.jsonl    # human input H3
    build_gold.py
    metrics.py
    run.py
  results/             # generated: metrics.json, metrics.md
  tests/
    test_chunking.py
    test_rrf.py
    test_metrics.py
    test_api.py
```

## 8. Testing

`pytest` must pass. Minimum tests:

- **Chunking:** overlap is respected, offsets map back to the exact source text, no empty chunks.
- **RRF:** a hand-built example with known ranks produces the expected fused order.
- **Metrics:** hit-rate and MRR on tiny hand-computed cases, including a miss and a tie.
- **API:** `/health` returns 200; `/ask` returns the response schema in retrieval-only mode using a tiny fixture corpus.

## 9. Milestones (3-hour plan)

| # | Milestone | Budget | Done when |
| --- | --- | --- | --- |
| M0 | Project scaffold, venv, dependency install, config, `.env.example` | 15 min | `pip install -r requirements.txt` works; imports succeed |
| M1 | Ingestion and chunking (+ chunking tests) | 25 min | `chunks.jsonl` produced; tests pass |
| M2 | Dense, BM25 and hybrid retrieval (+ RRF tests) | 30 min | All three modes return ranked results from a CLI check |
| M3 | FastAPI endpoint, generation, static page, retrieval-only fallback | 25 min | `/ask` works in both modes; page loads |
| M4 | Evaluation harness, gold offsets, metrics (+ metric tests); owner verifies labels (H3) | 40 min | `results/metrics.json` and `.md` generated from verified questions |
| M5 | Dockerfile, README, final test run | 20 min | `docker build` and `docker run` serve the app; README is accurate |
| Buffer | Fixes and surprises | 25 min | n/a |

## 10. Acceptance criteria (definition of done)

- [ ] `pytest` passes.
- [ ] `python -m rag.ingest && python -m rag.index` builds indices from `data/raw/`.
- [ ] `POST /ask` returns an answer with citations (LLM mode) or sources with `answer: null` (retrieval-only mode).
- [ ] `python -m eval.run` writes `results/metrics.json` and `results/metrics.md` covering `bm25`, `dense` and `hybrid`, over at least 40 verified questions.
- [ ] README contains: what it is, architecture diagram (a simple Mermaid block is fine), setup, usage, the metrics table copied from `results/metrics.md`, how labels were created (drafted vs verified counts), known limitations.
- [ ] `docker build` succeeds and the container serves `/health`.
- [ ] No secrets committed; no hard-coded metrics anywhere.

## 11. Risks and mitigations

| Risk | Mitigation |
| --- | --- |
| PyTorch or embedding model download is slow or large | Use the CPU wheel; use the small MiniLM model; bake it into the Docker image |
| PDF text extraction is messy (headers, columns, scanned pages) | Start with clean text or Markdown; log files with very low extracted text and exclude them, noting it |
| LLM key missing or rate-limited | Retrieval-only mode; evaluation does not depend on the LLM |
| Label quality is poor, making metrics meaningless | Human verification (H3); report drafted vs verified counts; exclude unfindable snippets |
| Hybrid does not beat dense | Report it honestly; discuss why in the README (for example, small corpus or exact-term questions) |
| Chunk boundaries split the gold answer | Offset-overlap hit definition (Section 5.7) instead of exact-chunk matching |
| Time overrun | Cut the static page and Docker polish first; never cut tests, evaluation, or honesty rules |

## 12. Resume line (to be filled only from real results)

Once `results/metrics.md` exists, the resume bullet is: "Improved hit-rate@5 from X% (dense-only) to Y% (hybrid BM25 + dense) on a N-question verified test set." Use the actual numbers, and if hybrid did not improve, state the measured comparison instead of claiming an improvement.

---

## 13. Git and GitHub rules for the build agent

The owner creates the GitHub repository and the first commit before the build starts (steps are in the chat). The agent works inside that existing local git repository.

### 13.1 Rules

1. Commit to the local repository **after every milestone** (M0 to M5), only when that milestone's tests pass.
2. **Do not run `git push`.** The owner pushes. Do not force-push, rewrite history, or change the remote.
3. Before each commit run `git status` and `git diff --staged`. Stage files explicitly by name or folder; do not use `git add .` blindly.
4. **Never commit:** `.env`, API keys or tokens, virtual environments, `__pycache__`, `index/` (generated), downloaded model caches, or `data/raw/` if the corpus is not redistributable. If a secret is ever staged, unstage it and tell the owner immediately.
5. One logical change per commit, with the message formats below. No "update" or "fix stuff" messages.
6. If tests fail, do not commit a green-looking milestone. Commit only working states, or prefix the message with `wip:` and say why.
7. Commit generated results (`results/metrics.json`, `results/metrics.md`) only when they were produced by `python -m eval.run` on the current code.

### 13.2 Commit plan

| After | Commit message |
| --- | --- |
| M0 | `chore: scaffold project structure, config and dependencies` |
| M1 | `feat(ingest): add document loading and overlapping chunking with tests` |
| M2 | `feat(retrieval): add BM25, dense (FAISS) and hybrid RRF retrieval with tests` |
| M3 | `feat(api): add FastAPI /ask endpoint, LLM generation and retrieval-only mode` |
| M3 | `feat(ui): add minimal static query page` |
| M4 | `feat(eval): add gold offset builder, metrics and evaluation runner with tests` |
| M4 | `docs(eval): add verified question set and generated metrics` |
| M5 | `build: add Dockerfile and container instructions` |
| M5 | `docs: write README with architecture, setup and results` |

The agent may split a milestone into more commits, but never merge two milestones into one.

### 13.3 `.gitignore` (create in M0)

```
.env
.venv/
venv/
__pycache__/
*.pyc
.pytest_cache/
index/
.cache/
hf_cache/
*.log
.DS_Store
# Uncomment if the corpus cannot be published:
# data/raw/
```

### 13.4 README requirements related to git

- State that the project was built with AI assistance (Antigravity) from a written PRD, and that the owner reviewed and understands the code.
- State how evaluation labels were produced (drafted versus human-verified counts).
- Include clone, install, ingest, index, run, evaluate and Docker commands exactly as tested.

### 13.5 Optional: continuous integration

If time remains, add `.github/workflows/ci.yml` that checks out the code, sets up Python 3.11, installs `requirements.txt`, and runs `pytest`. Commit as `ci: run tests on push`. Skip if installs are slow; never cut tests or evaluation for this.
