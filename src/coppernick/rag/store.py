"""A minimal in-memory vector store -- deliberately not a full vector database.

Scope reasoning: this hackathon build needs a working retrieval loop over a
few dozen to a few hundred documents (arXiv abstracts, public agency
bulletins), not millions of vectors -- brute-force cosine similarity over a
Python list is correct and fast enough at that scale, and adds zero
infrastructure dependency. Swap for a real vector DB (pgvector, Chroma, etc.)
if the corpus grows past a few thousand documents.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from ..schema import RetrievedPassage


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class VectorStore:
    """Holds (embedding, text, title, url) tuples and answers similarity queries."""

    def __init__(self) -> None:
        self._entries: list[dict] = []

    def add(self, text: str, embedding: list[float], title: str, url: str | None = None) -> None:
        self._entries.append({"text": text, "embedding": embedding, "title": title, "url": url})

    def search(self, query_embedding: list[float], top_k: int = 5) -> list[RetrievedPassage]:
        scored = [
            (entry, _cosine_similarity(query_embedding, entry["embedding"]))
            for entry in self._entries
        ]
        scored.sort(key=lambda pair: pair[1], reverse=True)
        return [
            RetrievedPassage(text=entry["text"], source_title=entry["title"], source_url=entry["url"], score=score)
            for entry, score in scored[:top_k]
        ]

    def __len__(self) -> int:
        return len(self._entries)

    def save(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(self._entries), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "VectorStore":
        store = cls()
        store._entries = json.loads(Path(path).read_text(encoding="utf-8"))
        return store
