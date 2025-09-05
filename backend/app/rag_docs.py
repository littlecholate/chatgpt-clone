# app/rag_docs.py
from __future__ import annotations
from pathlib import Path
from typing import List, Tuple
import numpy as np

_model = None
_chunks: List[Tuple[str, str]] | None = None   # (filename, chunk)
_embs: np.ndarray | None = None

_DOCS_DIR = (Path(__file__).resolve().parent.parent / "docs").resolve()

def _chunk_text(text: str, size: int = 800, overlap: int = 200) -> List[str]:
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

    files = list(_DOCS_DIR.rglob("*"))
    texts: List[str] = []
    pairs: List[Tuple[str, str]] = []

    for f in files:
        if f.suffix.lower() not in {".txt", ".md"}:
            continue
        try:
            txt = f.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for ch in _chunk_text(txt, 800, 200):
            pairs.append((f.name, ch))
            texts.append(ch)

    if not texts:
        _chunks, _embs = [], None
        return

    from sentence_transformers import SentenceTransformer
    _model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    _embs = _model.encode(texts, normalize_embeddings=True).astype("float32")
    _chunks = pairs

def rag_context(question: str, k: int = 5, max_words: int = 600) -> str:
    """
    Retrieve top-k chunks across ALL .txt/.md files in docs/.
    """
    _ensure_built()
    if not _chunks or _embs is None:
        return ""

    q = _model.encode([question], normalize_embeddings=True)[0].astype("float32")
    sims = _embs @ q
    k = max(1, min(k, len(_chunks)))
    idx = np.argpartition(-sims, k - 1)[:k]
    idx = idx[np.argsort(-sims[idx])]

    parts, used = [], 0
    for i in idx:
        fname, chunk = _chunks[int(i)]
        words = len(chunk.split())
        if used + words > max_words:
            break
        parts.append(f"[{fname}]\n{chunk}")
        used += words

    return "\n\n---\n\n".join(parts)