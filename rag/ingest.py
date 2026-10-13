"""Document ingestion and overlapping chunking."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import pypdf

import config


def chunk_text(
    text: str, chunk_size: int = config.CHUNK_SIZE, chunk_overlap: int = config.CHUNK_OVERLAP
) -> List[Tuple[int, int, str]]:
    """Splits text into overlapping chunks respecting boundary cues.

    Returns a list of (start_offset, end_offset, chunk_text).
    Guarantees:
      - text[start:end] == chunk_text
      - start < end
      - progress is strictly monotonic
      - overlap between adjacent chunks is respected
    """
    if not text:
        return []

    total_len = len(text)
    if total_len <= chunk_size:
        return [(0, total_len, text)]

    chunks: List[Tuple[int, int, str]] = []
    current_start = 0

    while current_start < total_len:
        if total_len - current_start <= chunk_size:
            chunk_str = text[current_start:total_len]
            chunks.append((current_start, total_len, chunk_str))
            break

        target_end = current_start + chunk_size
        search_start = current_start + max(1, chunk_size // 2)
        search_end = min(total_len, target_end + min(150, chunk_overlap))

        window = text[search_start:search_end]
        split_idx = -1

        # 1. Paragraph boundary: double newline
        p_idx = window.rfind("\n\n")
        if p_idx != -1:
            split_idx = search_start + p_idx + 2
        else:
            # 2. Sentence boundary: . / ? / ! followed by space or newline
            best_s = -1
            for punct in [". ", "? ", "! ", ".\n", "?\n", "!\n"]:
                pos = window.rfind(punct)
                if pos > best_s:
                    best_s = pos + len(punct)
            if best_s != -1:
                split_idx = search_start + best_s
            else:
                # 3. Single newline
                nl_idx = window.rfind("\n")
                if nl_idx != -1:
                    split_idx = search_start + nl_idx + 1
                else:
                    # 4. Word boundary: space
                    sp_idx = window.rfind(" ")
                    if sp_idx != -1:
                        split_idx = search_start + sp_idx + 1

        if split_idx == -1 or split_idx <= current_start or split_idx > total_len:
            split_idx = min(target_end, total_len)

        chunk_str = text[current_start:split_idx]
        chunks.append((current_start, split_idx, chunk_str))

        if split_idx >= total_len:
            break

        # Compute next start with approximate overlap
        target_next_start = max(current_start + 1, split_idx - chunk_overlap)
        next_start = target_next_start

        # Snap next_start forward to nearest word/boundary if feasible
        search_range = text[target_next_start : min(split_idx, target_next_start + 50)]
        space_pos = search_range.find(" ")
        if space_pos != -1:
            candidate = target_next_start + space_pos + 1
            if candidate < split_idx:
                next_start = candidate

        if next_start <= current_start:
            next_start = current_start + 1

        current_start = next_start

    return chunks


def extract_text_from_pdf(pdf_path: Path) -> Tuple[str, List[Tuple[int, int, int]]]:
    """Extracts text from PDF and tracks (start, end, page_number) spans.

    Returns:
      (full_document_text, page_spans)
    """
    reader = pypdf.PdfReader(str(pdf_path))
    doc_pieces: List[str] = []
    page_spans: List[Tuple[int, int, int]] = []
    current_offset = 0

    for page_idx, page in enumerate(reader.pages):
        page_num = page_idx + 1
        page_text = page.extract_text() or ""
        # Normalize carriage returns for cross-platform consistency
        page_text = page_text.replace("\r\n", "\n")
        start_offset = current_offset
        end_offset = current_offset + len(page_text)
        page_spans.append((start_offset, end_offset, page_num))
        doc_pieces.append(page_text)
        current_offset = end_offset

    full_text = "".join(doc_pieces)
    return full_text, page_spans


def find_page_number(start: int, page_spans: List[Tuple[int, int, int]]) -> Optional[int]:
    """Finds the 1-based page number containing the given character start offset."""
    for p_start, p_end, page_num in page_spans:
        if p_start <= start < p_end:
            return page_num
    if page_spans:
        return page_spans[-1][2]
    return None


def read_document(file_path: Path) -> Tuple[str, Optional[List[Tuple[int, int, int]]]]:
    """Reads a supported document (.pdf, .md, .txt)."""
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        return extract_text_from_pdf(file_path)
    elif suffix in [".md", ".txt"]:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            text = f.read().replace("\r\n", "\n")
        return text, None
    else:
        raise ValueError(f"Unsupported file format: {suffix}")


def ingest_corpus(
    raw_dir: Path = config.DATA_RAW_DIR,
    output_path: Path = config.CHUNKS_PATH,
    chunk_size: int = config.CHUNK_SIZE,
    chunk_overlap: int = config.CHUNK_OVERLAP,
) -> List[Dict[str, Any]]:
    """Ingests all documents from raw_dir and writes index/chunks.jsonl."""
    raw_dir.mkdir(parents=True, exist_ok=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    supported_exts = {".pdf", ".md", ".txt"}
    doc_paths = sorted([p for p in raw_dir.iterdir() if p.is_file() and p.suffix.lower() in supported_exts])

    all_chunks: List[Dict[str, Any]] = []

    for path in doc_paths:
        doc_id = path.name
        doc_text, page_spans = read_document(path)
        if not doc_text.strip():
            print(f"Warning: Document '{doc_id}' is empty or no text could be extracted. Skipping.")
            continue

        doc_chunks = chunk_text(doc_text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        for idx, (start, end, chunk_str) in enumerate(doc_chunks):
            page_num = find_page_number(start, page_spans) if page_spans else None
            chunk_record = {
                "chunk_id": f"{doc_id}#c{idx:04d}",
                "doc_id": doc_id,
                "page": page_num,
                "start": start,
                "end": end,
                "text": chunk_str,
            }
            all_chunks.append(chunk_record)

    # Persist chunks atomically / idempotently
    temp_path = output_path.with_suffix(".tmp")
    with open(temp_path, "w", encoding="utf-8") as f:
        for chunk in all_chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")
    temp_path.replace(output_path)

    print(f"Ingestion complete: {len(doc_paths)} documents processed, {len(all_chunks)} chunks written to {output_path}")
    return all_chunks


if __name__ == "__main__":
    ingest_corpus()
