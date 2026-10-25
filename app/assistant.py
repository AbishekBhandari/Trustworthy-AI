
"""Orchestrates the input and output guardrails."""

from app.input_guardrails import inspect_input
from app.knowledge_base import retrieve_documents
from app.output_guardrails import validate_output


SAFE_REFUSAL = {
    "answer": "I cannot assist with that request under the current safety policy.",
    "status": "refused",
    "sources": [],
    "warnings": ["input_guardrail_triggered"],
}


def generate_answer(
    question: str,
    reference_documents: list[dict[str, str]],
) -> dict:
    """Build a conservative extractive answer from retrieved passages."""
    if not reference_documents:
        return {
            "answer": "I do not have enough reference information to answer this question.",
            "status": "insufficient_evidence",
            "sources": [],
            "warnings": [],
        }

    answer = " ".join(document["text"] for document in reference_documents)

    return {
        "answer": answer,
        "status": "success",
        "sources": [document["id"] for document in reference_documents],
        "warnings": [],
    }


def answer_question(question: str) -> dict:
    """Run the complete guarded question-answering pipeline."""
    input_result = inspect_input(question)

    if not input_result.allowed:
        return SAFE_REFUSAL.copy()

    documents = retrieve_documents(input_result.text)

    if not documents:
        return {
            "answer": "I do not have enough reference information to answer this question.",
            "status": "insufficient_evidence",
            "sources": [],
            "warnings": ["no_relevant_reference"],
        }

    raw_response = generate_answer(input_result.text, documents)
    reference_text = " ".join(document["text"] for document in documents)

    result = validate_output(raw_response, reference_text)

    if not result.accepted:
        return result.response

    # Preserve the fact that the user's input was sanitized or flagged
    # for cautious handling without exposing the original PII.
    if input_result.action == "sanitize":
        result.response["warnings"].append("input_pii_redacted")
    elif input_result.action == "review":
        result.response["warnings"].append("sensitive_topic_review")

    return result.response
