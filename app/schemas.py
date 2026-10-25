
from typing import Literal

from pydantic import BaseModel, Field, ConfigDict


class AssistantResponse(BaseModel):
    """Strict response format returned by the AI assistant."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    answer: str = Field(min_length=1, max_length=3000)
    status: Literal["success", "refused", "insufficient_evidence"]
    sources: list[str] = Field(default_factory=list, max_length=10)
    warnings: list[str] = Field(default_factory=list, max_length=10)
