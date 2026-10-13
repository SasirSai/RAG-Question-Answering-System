import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

DATA_RAW_DIR = BASE_DIR / "data" / "raw"
INDEX_DIR = BASE_DIR / "index"
CHUNKS_PATH = INDEX_DIR / "chunks.jsonl"
FAISS_INDEX_PATH = INDEX_DIR / "faiss.index"
BM25_INDEX_PATH = INDEX_DIR / "bm25.pkl"

EVAL_DIR = BASE_DIR / "eval"
EVAL_QUESTIONS_PATH = EVAL_DIR / "questions.jsonl"
RESULTS_DIR = BASE_DIR / "results"
METRICS_JSON_PATH = RESULTS_DIR / "metrics.json"
METRICS_MD_PATH = RESULTS_DIR / "metrics.md"

CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "800"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "150"))

EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2")

RRF_K = int(os.getenv("RRF_K", "60"))
RRF_CANDIDATE_DEPTH = int(os.getenv("RRF_CANDIDATE_DEPTH", "50"))
DEFAULT_TOP_K = int(os.getenv("DEFAULT_TOP_K", "5"))

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "").strip().lower()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").strip()
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3").strip()

RANDOM_SEED = 42
