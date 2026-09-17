"""Retrieval orchestration, tested with embeddings mocked, store real."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from coppernick.rag.retrieve import index_documents, retrieve
from coppernick.rag.store import VectorStore


def test_index_documents_embeds_and_stores_each():
    store = VectorStore()
    docs = [
        {"title": "Doc A", "text": "about cyclones", "url": "http://a"},
        {"title": "Doc B", "summary": "about droughts", "url": "http://b"},
    ]
    with patch("coppernick.rag.retrieve.embed_document", side_effect=[[1, 0], [0, 1]]) as mock_embed:
        count = index_documents(MagicMock(), store, docs)

    assert count == 2
    assert len(store) == 2
    assert mock_embed.call_count == 2


def test_index_documents_skips_empty_text():
    store = VectorStore()
    docs = [{"title": "Empty Doc", "url": "http://empty"}]
    count = index_documents(MagicMock(), store, docs)
    assert count == 0
    assert len(store) == 0


def test_retrieve_embeds_query_and_searches_store():
    store = VectorStore()
    store.add("about cyclones", [1, 0], "Doc A", "http://a")

    with patch("coppernick.rag.retrieve.embed_query", return_value=[1, 0]) as mock_embed_query:
        results = retrieve(MagicMock(), store, "cyclone risk", top_k=1)

    assert len(results) == 1
    assert results[0].source_title == "Doc A"
    mock_embed_query.assert_called_once()
