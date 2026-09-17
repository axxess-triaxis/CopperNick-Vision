"""VectorStore -- pure logic, no mocks needed."""

from __future__ import annotations

import json

from coppernick.rag.store import VectorStore, _cosine_similarity


def test_cosine_similarity_identical_vectors():
    assert _cosine_similarity([1, 0, 0], [1, 0, 0]) == 1.0


def test_cosine_similarity_orthogonal_vectors():
    assert _cosine_similarity([1, 0], [0, 1]) == 0.0


def test_cosine_similarity_zero_vector_returns_zero():
    assert _cosine_similarity([0, 0], [1, 1]) == 0.0


def test_search_returns_most_similar_first():
    store = VectorStore()
    store.add("about cyclones", [1, 0, 0], "Doc A", "http://a")
    store.add("about droughts", [0, 1, 0], "Doc B", "http://b")
    store.add("mostly about cyclones", [0.9, 0.1, 0], "Doc C", "http://c")

    results = store.search([1, 0, 0], top_k=2)

    assert len(results) == 2
    assert results[0].source_title == "Doc A"
    assert results[1].source_title == "Doc C"
    assert results[0].score >= results[1].score


def test_save_and_load_roundtrip(tmp_path):
    store = VectorStore()
    store.add("text one", [1, 2, 3], "Title One", "http://one")
    path = tmp_path / "store.json"
    store.save(path)

    loaded = VectorStore.load(path)

    assert len(loaded) == 1
    result = loaded.search([1, 2, 3], top_k=1)
    assert result[0].source_title == "Title One"


def test_empty_store_returns_no_results():
    store = VectorStore()
    assert store.search([1, 0, 0]) == []
