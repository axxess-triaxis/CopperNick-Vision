"""Ties embeddings + the vector store together: index documents, then retrieve."""

from __future__ import annotations

from google import genai

from ..schema import RetrievedPassage
from .embeddings import embed_document, embed_query
from .store import VectorStore


def index_documents(client: genai.Client, store: VectorStore, documents: list[dict]) -> int:
    """Embed and add each document (dict with 'text'/'summary', 'title', 'url')
    to the store. Returns the number of documents indexed.
    """

    count = 0
    for doc in documents:
        text = doc.get("text") or doc.get("summary") or ""
        if not text:
            continue
        embedding = embed_document(client, text)
        store.add(text=text, embedding=embedding, title=doc["title"], url=doc.get("url"))
        count += 1
    return count


def retrieve(client: genai.Client, store: VectorStore, query: str, top_k: int = 5) -> list[RetrievedPassage]:
    """Embed a query and return the top-k most similar passages from the store."""

    query_embedding = embed_query(client, query)
    return store.search(query_embedding, top_k=top_k)
