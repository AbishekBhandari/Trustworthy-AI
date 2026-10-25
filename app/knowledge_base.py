
"""Small local knowledge base for the guardrails demonstration."""

import json
import re
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "reference_docs.json"


def load_documents() -> list[dict[str, str]]:
    with DATA_PATH.open("r", encoding="utf-8") as file:
        documents = json.load(file)

    if not isinstance(documents, list):
        raise ValueError("Reference data must be a list of documents.")

    return documents


def retrieve_documents(
    question: str,
    documents: list[dict[str, str]] | None = None,
    limit: int = 2,
) -> list[dict[str, str]]:
    """Return documents ranked by simple query-word overlap."""
    if documents is None:
        documents = load_documents()

    query_words = {
        word for word in re.findall(r"\b[a-zA-Z0-9]+\b", question.lower())
        if len(word) > 2
    }

    ranked = []
    for document in documents:
        text = document.get("text", "")
        doc_words = set(
            re.findall(r"\b[a-zA-Z0-9]+\b", text.lower())
        )
        score = len(query_words & doc_words)

        if score:
            ranked.append((score, document))

    ranked.sort(key=lambda item: item[0], reverse=True)
    return [document for _, document in ranked[:limit]]
