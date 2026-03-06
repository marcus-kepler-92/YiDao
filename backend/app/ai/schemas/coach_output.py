"""Pydantic models for Coach Agent structured output."""

from pydantic import BaseModel, Field


class ActionItem(BaseModel):
    """A single recommended action."""

    id: str
    description: str
    when_suitable: str
    action: str
    why: str
    how: str


class CoachOutput(BaseModel):
    """Structured output schema for the Coach Agent LLM call (PRD §5.2)."""

    situation: str = Field(description="局面解读 — 对用户当前处境的描述")
    advantages: list[str] = Field(description="优势 — 用户已有的积极因素")
    blindspots: list[str] = Field(description="盲点 — 用户可能忽略的方面")
    actions: list[ActionItem] = Field(description="行动建议列表")
