"""Gemini embedding wrappers, tested with the genai client mocked."""

from __future__ import annotations

from unittest.mock import MagicMock

from coppernick.rag.embeddings import EMBEDDING_MODEL, embed_document, embed_query


def test_embed_document_uses_retrieval_document_task_type():
    mock_client = MagicMock()
    mock_client.models.embed_content.return_value = MagicMock(
        embeddings=[MagicMock(values=[0.1, 0.2, 0.3])]
    )

    result = embed_document(mock_client, "some document text")

    assert result == [0.1, 0.2, 0.3]
    call_kwargs = mock_client.models.embed_content.call_args.kwargs
    assert call_kwargs["model"] == EMBEDDING_MODEL
    assert call_kwargs["config"].task_type == "RETRIEVAL_DOCUMENT"


def test_embed_query_uses_retrieval_query_task_type():
    mock_client = MagicMock()
    mock_client.models.embed_content.return_value = MagicMock(
        embeddings=[MagicMock(values=[0.4, 0.5, 0.6])]
    )

    result = embed_query(mock_client, "some query text")

    assert result == [0.4, 0.5, 0.6]
    call_kwargs = mock_client.models.embed_content.call_args.kwargs
    assert call_kwargs["config"].task_type == "RETRIEVAL_QUERY"
