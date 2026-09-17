"""Ontology store, tested with the genai client mocked for extraction and
real for the query/persistence logic."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

from coppernick.schema import KnowledgeAssertion
from coppernick.sky.ontology import OntologyStore, extract_assertions


def test_extract_assertions_parses_structured_response():
    mock_client = MagicMock()
    raw = {
        "assertions": [
            {"subject": "Cyclone Amphan", "relation": "recorded peak wind speed of", "object": "60 kt", "confidence": 0.95}
        ]
    }
    mock_client.interactions.create.return_value = MagicMock(output_text=json.dumps(raw))

    result = extract_assertions(mock_client, "Amphan peaked at 60 kt.", source="track-data")

    assert len(result) == 1
    assert result[0].subject == "Cyclone Amphan"
    assert result[0].source == "track-data"
    assert result[0].confidence == 0.95


def test_extract_assertions_defaults_confidence_when_missing():
    mock_client = MagicMock()
    raw = {"assertions": [{"subject": "A", "relation": "relates to", "object": "B"}]}
    mock_client.interactions.create.return_value = MagicMock(output_text=json.dumps(raw))

    result = extract_assertions(mock_client, "text", source="src")

    assert result[0].confidence == 1.0


def test_ontology_store_query_filters_by_subject_relation_object():
    store = OntologyStore()
    store.add(KnowledgeAssertion(subject="Chennai", relation="experienced", object="flooding", source="s1"))
    store.add(KnowledgeAssertion(subject="Mumbai", relation="experienced", object="flooding", source="s2"))

    results = store.query(subject="chennai")

    assert len(results) == 1
    assert results[0].subject == "Chennai"


def test_ontology_store_save_and_load_roundtrip(tmp_path):
    store = OntologyStore()
    store.add(KnowledgeAssertion(subject="A", relation="R", object="B", source="src"))
    path = tmp_path / "ontology.json"
    store.save(path)

    loaded = OntologyStore.load(path)

    assert len(loaded) == 1
    assert loaded.query(subject="A")[0].object == "B"


def test_ontology_store_add_all():
    store = OntologyStore()
    store.add_all([
        KnowledgeAssertion(subject="A", relation="R", object="B", source="s"),
        KnowledgeAssertion(subject="C", relation="R", object="D", source="s"),
    ])
    assert len(store) == 2
