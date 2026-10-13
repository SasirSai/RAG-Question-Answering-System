"""Evaluation runner benchmarking BM25, Dense, and Hybrid retrieval strategies."""

import datetime
import json
import time
from pathlib import Path
from typing import Any, Dict, List

import config
from eval.build_gold import build_gold_offsets
from eval.metrics import aggregate_metrics, evaluate_query_hits
from rag.retrieve import get_retriever


def run_evaluation(
    questions_path: Path = config.EVAL_QUESTIONS_PATH,
    metrics_json_path: Path = config.METRICS_JSON_PATH,
    metrics_md_path: Path = config.METRICS_MD_PATH,
) -> Dict[str, Any]:
    """Runs evaluation over verified questions for bm25, dense, and hybrid modes."""
    # 1. Build and validate gold offsets
    valid_records, excluded = build_gold_offsets(questions_path)

    # 2. Filter to verified: true questions
    verified_questions = [q for q in valid_records if q.get("verified") is True]
    count = len(verified_questions)

    print(f"\nEvaluating over {count} verified questions (minimum target: 40)...")
    if count < 40:
        print(f"WARNING: Verified question count is {count}, which is below the 40 question requirement!")

    if count == 0:
        raise ValueError("No verified questions with valid gold offsets found.")

    retriever = get_retriever()
    modes = ["bm25", "dense", "hybrid"]
    results_by_mode: Dict[str, Dict[str, Any]] = {}

    for mode in modes:
        print(f"Evaluating mode '{mode}' across {count} questions...")
        query_metrics: List[Dict[str, float]] = []
        latencies_ms: List[float] = []

        for q in verified_questions:
            q_text = q["question"]
            gold_doc = q["gold_doc_id"]
            gold_start = q["gold_start"]
            gold_end = q["gold_end"]

            t0 = time.perf_counter()
            retrieved = retriever.retrieve(query=q_text, mode=mode, k=10)
            latency = (time.perf_counter() - t0) * 1000.0
            latencies_ms.append(latency)

            chunks = [c for c, _ in retrieved]
            qm = evaluate_query_hits(chunks, gold_doc, gold_start, gold_end)
            query_metrics.append(qm)

        mode_summary = aggregate_metrics(query_metrics, latencies_ms)
        results_by_mode[mode] = mode_summary
        print(
            f"  {mode}: Hit@1={mode_summary['hit_rate_at_1']:.3f}, "
            f"Hit@3={mode_summary['hit_rate_at_3']:.3f}, "
            f"Hit@5={mode_summary['hit_rate_at_5']:.3f}, "
            f"MRR={mode_summary['mrr']:.3f}, "
            f"Median={mode_summary['median_latency_ms']:.1f}ms, "
            f"P95={mode_summary['p95_latency_ms']:.1f}ms"
        )

    # Prepare outputs
    timestamp_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    config_snapshot = {
        "CHUNK_SIZE": config.CHUNK_SIZE,
        "CHUNK_OVERLAP": config.CHUNK_OVERLAP,
        "EMBEDDING_MODEL_NAME": config.EMBEDDING_MODEL_NAME,
        "RRF_K": config.RRF_K,
        "RRF_CANDIDATE_DEPTH": config.RRF_CANDIDATE_DEPTH,
        "RANDOM_SEED": config.RANDOM_SEED,
    }

    metrics_payload = {
        "timestamp": timestamp_iso,
        "question_count": count,
        "below_minimum_target": count < 40,
        "config": config_snapshot,
        "modes": results_by_mode,
    }

    # Write metrics.json
    metrics_json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(metrics_json_path, "w", encoding="utf-8") as f:
        json.dump(metrics_payload, f, indent=2)
    print(f"\nSaved metrics JSON to {metrics_json_path}")

    # Write metrics.md
    md_content = generate_markdown_report(metrics_payload, total_corpus_chunks=len(retriever.chunks))
    with open(metrics_md_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"Saved metrics Markdown to {metrics_md_path}")

    return metrics_payload


def generate_markdown_report(payload: Dict[str, Any], total_corpus_chunks: int) -> str:
    """Generates GitHub-flavored markdown table and report from metrics payload."""
    count = payload["question_count"]
    warning = f"\n> [!WARNING]\n> Only {count} verified questions were evaluated (target minimum is 40).\n" if payload.get("below_minimum_target") else ""
    ts = payload["timestamp"]
    modes = payload["modes"]

    lines = [
        "# Retrieval Strategy Evaluation Results",
        "",
        warning,
        f"- **Timestamp:** `{ts}`",
        f"- **Verified Questions Evaluated:** `{count}`",
        f"- **Indexed Chunks:** `{total_corpus_chunks}`",
        f"- **Embedding Model:** `{payload['config']['EMBEDDING_MODEL_NAME']}`",
        f"- **RRF Parameters:** `k={payload['config']['RRF_K']}`, `depth={payload['config']['RRF_CANDIDATE_DEPTH']}`",
        "",
        "| Retrieval Mode | Hit-Rate@1 | Hit-Rate@3 | Hit-Rate@5 | MRR (Top 10) | Median Latency (ms) | P95 Latency (ms) |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]

    for mode_name in ["bm25", "dense", "hybrid"]:
        m = modes[mode_name]
        lines.append(
            f"| `{mode_name}` | {m['hit_rate_at_1']:.4f} | {m['hit_rate_at_3']:.4f} | "
            f"{m['hit_rate_at_5']:.4f} | {m['mrr']:.4f} | {m['median_latency_ms']:.2f} ms | {m['p95_latency_ms']:.2f} ms |"
        )

    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    run_evaluation()
