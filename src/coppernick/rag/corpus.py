"""Public corpus ingestion -- climate/disaster-response research only, fully
open sources, no access-restricted or classified material.

arXiv's public Atom API (no key required) verified directly (checked
2026-09-17): `https://export.arxiv.org/api/query?search_query=...` -- note
the `https` scheme; the `http` variant 301-redirects to it.
"""

from __future__ import annotations

from xml.etree import ElementTree

import httpx

from ..schema import RetrievedPassage

ARXIV_API_URL = "https://export.arxiv.org/api/query"
_ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}


def fetch_arxiv_abstracts(query: str, max_results: int = 10, timeout: float = 15.0) -> list[dict]:
    """Fetch paper title/summary/link/id for a search query against arXiv.

    Returns plain dicts (not yet embedded) -- the caller decides whether to
    chunk further before embedding via `rag.embeddings.embed_document`.
    """

    response = httpx.get(
        ARXIV_API_URL,
        params={"search_query": f"all:{query}", "start": 0, "max_results": max_results},
        timeout=timeout,
    )
    response.raise_for_status()
    root = ElementTree.fromstring(response.text)

    papers = []
    for entry in root.findall("atom:entry", _ATOM_NS):
        title = entry.findtext("atom:title", default="", namespaces=_ATOM_NS).strip()
        summary = entry.findtext("atom:summary", default="", namespaces=_ATOM_NS).strip()
        arxiv_id = entry.findtext("atom:id", default="", namespaces=_ATOM_NS).strip()
        papers.append({"title": title, "summary": summary, "url": arxiv_id})
    return papers


def register_source_documents(
    documents: list[dict],
) -> list[RetrievedPassage]:
    """Convert raw fetched documents (with 'title', 'summary'/'text', 'url' keys)
    into the shape used before embedding. This does not embed or store them --
    see rag.retrieve.index_documents for that step.
    """

    passages = []
    for doc in documents:
        text = doc.get("summary") or doc.get("text") or ""
        passages.append(RetrievedPassage(text=text, source_title=doc["title"], source_url=doc.get("url"), score=0.0))
    return passages
