# app/rag_min.py
from __future__ import annotations
from pathlib import Path
from typing import List, Tuple
import numpy as np

# Lazy imports so first call is fast if model is already cached
_model = None
_chunks: List[str] | None = None
_embs: np.ndarray | None = None

# Hard-coded path: only this file is ever read
_TEST_FILE = (Path(__file__).resolve().parent.parent / "docs" / "test.txt").resolve()

def _chunk_text(text: str, size: int = 800, overlap: int = 200) -> List[str]:
    # minimal non-regex chunker
    if size <= 0:
        return [text]
    out, i, n = [], 0, len(text)
    while i < n:
        j = min(i + size, n)
        out.append(text[i:j])
        if j == n:
            break
        i = max(0, j - overlap)
    return out

def _ensure_built():
    global _model, _chunks, _embs
    if _chunks is not None and _embs is not None and _model is not None:
        return
    # 1) read test.txt (if missing, just act as empty)
    if not _TEST_FILE.exists():
        _chunks, _embs = [], None
        return
    text = _TEST_FILE.read_text(encoding="utf-8", errors="ignore")
    _chunks = _chunk_text(text, size=800, overlap=200)
    if not _chunks:
        _embs = None
        return
    # 2) embed
    from sentence_transformers import SentenceTransformer
    _model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    _embs = _model.encode(_chunks, normalize_embeddings=True).astype("float32")

def rag_context(question: str, k: int = 3, max_words: int = 400) -> str:
    """
    Returns a small context string pulled ONLY from docs/test.txt.
    If the file is missing or empty, returns "".
    """
    _ensure_built()
    if not _chunks or _embs is None:
        return ""

    # encode query
    q = _model.encode([question], normalize_embeddings=True)[0].astype("float32")
    sims = _embs @ q  # cosine similarity on normalized vectors
    k = max(1, min(k, len(_chunks)))
    idx = np.argpartition(-sims, k - 1)[:k]
    idx = idx[np.argsort(-sims[idx])]

    # assemble small context budget
    picked = []
    used = 0
    for i in idx:
        chunk = _chunks[int(i)]
        words = len(chunk.split())
        if used + words > max_words:
            break
        picked.append(chunk)
        used += words

    if not picked:
        return ""
    rel = _TEST_FILE.name  # show just "test.txt"
    return f"[Source: {rel}]\n" + "\n---\n".join(picked)