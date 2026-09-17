"""Gemini text embeddings for the RAG store.

API shape (`client.models.embed_content(model=, contents=, config=)`,
`response.embeddings[0].values`, `EmbedContentConfig(task_type=...)`)
confirmed by directly introspecting the installed google-genai SDK (checked
2026-09-17) -- not guessed.

Uses `gemini-embedding-001` (not the newer `gemini-embedding-2`) deliberately:
-001 has simple one-embedding-per-input semantics via `task_type` config,
while -2 aggregates multiple inputs into a single embedding by default and
expects task instructions as prompt-text prefixes rather than a config field
-- the wrong tool for embedding many independent document chunks one at a time.
"""

from __future__ import annotations

from google import genai
from google.genai import types

EMBEDDING_MODEL = "gemini-embedding-001"


def embed_document(client: genai.Client, text: str) -> list[float]:
    """Embed one document/chunk for storage in the RAG index."""

    response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text,
        config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT"),
    )
    return response.embeddings[0].values


def embed_query(client: genai.Client, text: str) -> list[float]:
    """Embed a search query -- uses a different task_type than document
    embedding since retrieval is asymmetric (query phrasing differs from
    document phrasing)."""

    response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text,
        config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY"),
    )
    return response.embeddings[0].values
