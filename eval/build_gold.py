"""Locates verbatim gold_snippets in raw documents and computes gold offsets."""

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

import config
from rag.ingest import read_document

GOLD_QUESTIONS_PATH = config.EVAL_DIR / "gold_questions.jsonl"


def build_gold_offsets(
    questions_path: Path = config.EVAL_QUESTIONS_PATH,
    output_path: Path = GOLD_QUESTIONS_PATH,
    raw_dir: Path = config.DATA_RAW_DIR,
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Locates each gold_snippet in its corresponding document.

    Any snippet that cannot be found is reported and excluded.
    Returns:
      (valid_records_with_offsets, list_of_excluded_ids)
    """
    if not questions_path.exists():
        raise FileNotFoundError(f"Questions file not found: {questions_path}")

    questions: List[Dict[str, Any]] = []
    with open(questions_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                questions.append(json.loads(line))

    # Cache document texts in memory
    doc_cache: Dict[str, str] = {}
    valid_records: List[Dict[str, Any]] = []
    excluded_ids: List[str] = []

    for q in questions:
        q_id = q.get("id", "unknown")
        doc_id = q.get("gold_doc_id")
        snippet = q.get("gold_snippet", "").strip()

        if not doc_id or not snippet:
            print(f"Warning: Question {q_id} missing doc_id or snippet. Excluding.")
            excluded_ids.append(q_id)
            continue

        if doc_id not in doc_cache:
            doc_path = raw_dir / doc_id
            if not doc_path.exists():
                print(f"ERROR: Document {doc_id} does not exist in {raw_dir}. Excluding {q_id}.")
                excluded_ids.append(q_id)
                continue
            text, _ = read_document(doc_path)
            doc_cache[doc_id] = text

        doc_text = doc_cache[doc_id]
        pos = doc_text.find(snippet)
        if pos == -1:
            print(f"ERROR: Snippet for {q_id} not found in {doc_id}. Excluded snippet: '{snippet[:60]}...'")
            excluded_ids.append(q_id)
            continue

        updated = dict(q)
        updated["gold_start"] = pos
        updated["gold_end"] = pos + len(snippet)
        valid_records.append(updated)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for r in valid_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(
        f"Gold offset build complete: {len(questions)} evaluated, "
        f"{len(valid_records)} valid with offsets written to {output_path}, "
        f"{len(excluded_ids)} excluded."
    )
    return valid_records, excluded_ids


if __name__ == "__main__":
    build_gold_offsets()
