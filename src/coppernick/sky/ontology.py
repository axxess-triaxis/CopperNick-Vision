"""Memory / ontology store: entity-relation-entity facts extracted from
observations and research, queryable for cross-session context.

Deliberately a flat triple store (subject, relation, object), not a full
RDF/OWL ontology or graph database -- this hackathon build needs facts that
persist and can be filtered/joined across sessions (e.g. "what have we
observed about this coastline before"), not formal ontological reasoning
(subsumption, inference rules, SPARQL). A triple store gets the useful
80% -- structured, queryable, source-attributed facts -- without the
engineering cost of a real reasoner. See docs/ARCHITECTURE.md.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from google import genai

from ..agent import GEMINI_CALL_TIMEOUT_SECONDS
from ..schema import KnowledgeAssertion

SYSTEM_PROMPT = """Extract concrete factual assertions from the given text as \
subject-relation-object triples. Only extract facts actually stated or directly observed in \
the text -- never infer or invent a fact not present. Keep subjects and objects as short, \
specific noun phrases (a place name, a storm name, a measurable quantity) and relations as \
short verb phrases (e.g. "recorded wind speed of", "is located near", "was observed on")."""


def extract_assertions(client: genai.Client, text: str, source: str) -> list[KnowledgeAssertion]:
    """Use Gemini to pull structured facts out of free text (a research
    abstract, a vision/night-sky observation summary, etc.)."""

    schema = {
        "type": "object",
        "properties": {
            "assertions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "subject": {"type": "string"},
                        "relation": {"type": "string"},
                        "object": {"type": "string"},
                        "confidence": {"type": "number"},
                    },
                    "required": ["subject", "relation", "object"],
                },
            }
        },
        "required": ["assertions"],
    }

    interaction = client.interactions.create(
        model=os.environ.get("COPPERNICK_GEMINI_MODEL", "gemini-3.8-flash"),
        input=[
            {"type": "text", "text": SYSTEM_PROMPT},
            {"type": "text", "text": f"Text:\n{text}"},
        ],
        response_format={"type": "text", "mime_type": "application/json", "schema": schema},
        timeout=GEMINI_CALL_TIMEOUT_SECONDS,
    )
    raw = json.loads(interaction.output_text)
    return [
        KnowledgeAssertion(
            subject=a["subject"],
            relation=a["relation"],
            object=a["object"],
            source=source,
            confidence=a.get("confidence", 1.0),
        )
        for a in raw["assertions"]
    ]


class OntologyStore:
    """Append-only local store of KnowledgeAssertions, JSON-file-backed."""

    def __init__(self) -> None:
        self._assertions: list[KnowledgeAssertion] = []

    def add(self, assertion: KnowledgeAssertion) -> None:
        self._assertions.append(assertion)

    def add_all(self, assertions: list[KnowledgeAssertion]) -> None:
        self._assertions.extend(assertions)

    def query(
        self,
        subject: str | None = None,
        relation: str | None = None,
        obj: str | None = None,
    ) -> list[KnowledgeAssertion]:
        def matches(a: KnowledgeAssertion) -> bool:
            if subject and subject.lower() not in a.subject.lower():
                return False
            if relation and relation.lower() not in a.relation.lower():
                return False
            if obj and obj.lower() not in a.object.lower():
                return False
            return True

        return [a for a in self._assertions if matches(a)]

    def __len__(self) -> int:
        return len(self._assertions)

    def save(self, path: str | Path) -> None:
        Path(path).write_text(
            json.dumps([a.model_dump(mode="json") for a in self._assertions]), encoding="utf-8"
        )

    @classmethod
    def load(cls, path: str | Path) -> "OntologyStore":
        store = cls()
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        store._assertions = [KnowledgeAssertion.model_validate(a) for a in raw]
        return store
