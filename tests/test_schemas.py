
import pytest
from pydantic import ValidationError

from app.schemas import AssistantResponse


def test_valid_response():
    response = AssistantResponse(
        answer="An index improves data retrieval.",
        status="success",
        sources=["database_basics"],
        warnings=[],
    )
    assert response.status == "success"


def test_missing_answer_rejected():
    with pytest.raises(ValidationError):
        AssistantResponse(status="success")


def test_invalid_status_rejected():
    with pytest.raises(ValidationError):
        AssistantResponse(
            answer="Hello",
            status="approved",
        )


def test_extra_field_rejected():
    with pytest.raises(ValidationError):
        AssistantResponse(
            answer="Hello",
            status="success",
            internal_secret="hidden",
        )


def test_empty_answer_rejected():
    with pytest.raises(ValidationError):
        AssistantResponse(
            answer="",
            status="success",
        )


def test_wrong_answer_type_rejected():
    with pytest.raises(ValidationError):
        AssistantResponse(
            answer=123,
            status="success",
        )
