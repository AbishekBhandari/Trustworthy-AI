
from app.output_guardrails import (
    validate_groundedness,
    validate_output,
)


REFERENCE = (
    "Python is a programming language. "
    "Python supports functions and modules."
)


def test_supported_claim_passes():
    ok, unsupported = validate_groundedness(
        "Python is a programming language.",
        REFERENCE,
    )
    assert ok
    assert unsupported == []


def test_unrelated_claim_fails():
    ok, unsupported = validate_groundedness(
        "Elephants migrate across distant tropical forests.",
        REFERENCE,
    )
    assert not ok
    assert unsupported


def test_invalid_schema_returns_fallback():
    result = validate_output(
        {"answer": "Hello", "status": "unknown"},
        REFERENCE,
    )
    assert not result.accepted
    assert "schema_invalid" in result.flags
    assert result.response["status"] == "insufficient_evidence"


def test_unsupported_output_returns_fallback():
    result = validate_output(
        {
            "answer": "Elephants migrate across distant tropical forests.",
            "status": "success",
            "sources": [],
            "warnings": [],
        },
        REFERENCE,
    )
    assert not result.accepted
    assert "groundedness_failed" in result.flags


def test_output_email_is_redacted():
    result = validate_output(
        {
            "answer": "Contact person@example.com for details about Python programming language.",
            "status": "success",
            "sources": ["python_docs"],
            "warnings": [],
        },
        REFERENCE,
    )
    assert "person@example.com" not in result.response["answer"]
    assert "output_pii_redacted" in result.flags


def test_empty_reference_rejects_claims():
    ok, unsupported = validate_groundedness(
        "Python is a programming language.",
        "",
    )
    assert not ok
    assert unsupported
