
"""Output guardrails for schema, groundedness, and sensitive information."""

import re
from dataclasses import dataclass, field
from typing import Any

from pydantic import ValidationError

from app.input_guardrails import detect_pii, redact_pii
from app.schemas import AssistantResponse


@dataclass
class OutputCheck:
    accepted: bool
    response: dict[str, Any]
    flags: list[str] = field(default_factory=list)
    unsupported_claims: list[str] = field(default_factory=list)



def validate_groundedness(
    answer: str,
    reference_text: str,
) -> tuple[bool, list[str]]:
    """Check lexical support and flag simple negation conflicts.

    This is a heuristic, not a full semantic fact-checker.
    """
    if not reference_text.strip():
        return False, [answer]

    sentences = re.split(r"(?<=[.!?])\s+", answer.strip())
    reference_sentences = re.split(
        r"(?<=[.!?])\s+", reference_text.strip()
    )

    def words(text: str) -> set[str]:
        return set(re.findall(r"\b[a-zA-Z0-9']+\b", text.lower()))

    negations = {
        "not", "no", "never", "neither", "cannot", "can't",
        "isn't", "aren't", "wasn't", "weren't", "doesn't",
        "don't", "didn't", "without"
    }

    unsupported = []

    for sentence in sentences:
        sentence_words = words(sentence)
        meaningful_words = {
            word for word in sentence_words if len(word) > 3
        }

        if not meaningful_words:
            continue

        best_overlap = 0.0
        best_reference = None

        for reference_sentence in reference_sentences:
            reference_words = words(reference_sentence)
            reference_meaningful = {
                word for word in reference_words if len(word) > 3
            }

            if not reference_meaningful:
                continue

            overlap = (
                len(meaningful_words & reference_meaningful)
                / len(meaningful_words)
            )

            if overlap > best_overlap:
                best_overlap = overlap
                best_reference = reference_sentence

        if best_reference is None or best_overlap < 0.5:
            unsupported.append(sentence)
            continue

        answer_negated = bool(sentence_words & negations)
        reference_negated = bool(words(best_reference) & negations)

        # Reject high-overlap claims when simple negation differs.
        if (
            best_overlap >= 0.5
            and answer_negated != reference_negated
        ):
            unsupported.append(sentence)

    return len(unsupported) == 0, unsupported



def validate_output(
    raw_response: dict[str, Any],
    reference_text: str,
) -> OutputCheck:
    """Validate structure, groundedness, and output privacy.

    Invalid responses receive a safe fallback. PII is redacted before
    returning a response. The caller should log flags without logging PII.
    """
    try:
        response = AssistantResponse.model_validate(raw_response)
    except (ValidationError, ValueError, TypeError):
        return OutputCheck(
            accepted=False,
            response={
                "answer": "I cannot provide a validated response to this request.",
                "status": "insufficient_evidence",
                "sources": [],
                "warnings": ["output_validation_failed"],
            },
            flags=["schema_invalid", "safe_fallback"],
        )

    flags: list[str] = []

    # Check for PII before checking groundedness.
    if detect_pii(response.answer):
        redacted_answer, _ = redact_pii(response.answer)
        response = response.model_copy(update={"answer": redacted_answer})
        flags.append("output_pii_redacted")

    grounded, unsupported = validate_groundedness(
        response.answer,
        reference_text,
    )

    if not grounded:
        flags.append("groundedness_failed")
        return OutputCheck(
            accepted=False,
            response={
                "answer": "I could not verify the generated answer against the provided reference information.",
                "status": "insufficient_evidence",
                "sources": [],
                "warnings": ["groundedness_validation_failed"],
            },
            flags=flags + ["safe_fallback"],
            unsupported_claims=unsupported,
        )

    return OutputCheck(
        accepted=True,
        response=response.model_dump(),
        flags=flags,
    )
