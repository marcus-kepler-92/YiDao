"""Pydantic models for Parse Agent structured output."""

from pydantic import BaseModel, Field

from app.ai.state import SafetyFlag


class ParseResult(BaseModel):
    """Structured output schema for the Parse Agent LLM call."""

    intent: str = Field(description="User intent category")
    slots_delta: dict[str, str] = Field(
        default_factory=dict,
        description="New or updated slot key-value pairs extracted from the message",
    )
    safety_flags: list[SafetyFlag] = Field(
        default_factory=list,
        description="Detected safety concerns, if any",
    )
    core_issue_summary: str = Field(
        default="",
        description="One-sentence summary of the user's core issue",
    )
