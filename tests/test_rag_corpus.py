"""arXiv corpus fetcher, tested with the HTTP call mocked via respx."""

from __future__ import annotations

import httpx
import respx

from coppernick.rag.corpus import ARXIV_API_URL, fetch_arxiv_abstracts, register_source_documents

SAMPLE_ATOM_RESPONSE = """<?xml version='1.0' encoding='UTF-8'?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>http://arxiv.org/abs/1234.5678v1</id>
    <title>Cyclone Risk Modeling in Coastal Regions</title>
    <summary>A study of cyclone risk using historical track data.</summary>
  </entry>
  <entry>
    <id>http://arxiv.org/abs/8765.4321v1</id>
    <title>Machine Learning for Disaster Response</title>
    <summary>Applying ML models to disaster response coordination.</summary>
  </entry>
</feed>
"""


@respx.mock
def test_fetch_arxiv_abstracts_parses_entries():
    respx.get(ARXIV_API_URL).mock(return_value=httpx.Response(200, text=SAMPLE_ATOM_RESPONSE))

    papers = fetch_arxiv_abstracts("cyclone risk", max_results=2)

    assert len(papers) == 2
    assert papers[0]["title"] == "Cyclone Risk Modeling in Coastal Regions"
    assert "cyclone risk" in papers[0]["summary"]
    assert papers[0]["url"] == "http://arxiv.org/abs/1234.5678v1"


@respx.mock
def test_fetch_arxiv_abstracts_raises_on_http_error():
    respx.get(ARXIV_API_URL).mock(return_value=httpx.Response(500))
    try:
        fetch_arxiv_abstracts("cyclone risk")
        assert False, "expected HTTPStatusError"
    except httpx.HTTPStatusError:
        pass


def test_register_source_documents_converts_to_passages():
    docs = [{"title": "Doc A", "summary": "Some summary", "url": "http://a"}]
    passages = register_source_documents(docs)
    assert len(passages) == 1
    assert passages[0].source_title == "Doc A"
    assert passages[0].text == "Some summary"
