"""
LangGraph shared state — single Pydantic model used by all graph nodes.

Every node reads from and writes to this state.
Add fields as the graph grows; keep this file as the single source of truth.
"""

from __future__ import annotations

import enum
from typing import Any

from langchain_core.messages import BaseMessage
from pydantic import BaseModel, Field


class BucketStage(str, enum.Enum):
    """Bucket 状态机阶段 (PRD §13)"""

    COLLECTING = "collecting"
    FOCUSING = "focusing"
    COACHING_PROBE = "coaching_probe"
    COACHING_DEEP = "coaching_deep"
    SAFETY_OVERRIDE = "safety_override"
    CLOSED = "closed"


class SafetyFlag(str, enum.Enum):
    SELF_HARM = "self_harm"
    HARM_OTHERS = "harm_others"
    ILLEGAL = "illegal"


class GraphState(BaseModel):
    """Shared state flowing through the LangGraph StateGraph."""

    # --- Conversation ---
    messages: list[BaseMessage] = Field(default_factory=list)
    user_message: str = ""

    # --- Parse result ---
    intent: str = ""
    slots_delta: dict[str, Any] = Field(default_factory=dict)
    safety_flags: list[SafetyFlag] = Field(default_factory=list)

    # --- Bucket ---
    bucket_id: int | None = None
    scene: str = ""
    pattern_name: str = ""
    stage: BucketStage = BucketStage.COLLECTING
    completeness: float = 0.0

    # --- Coach output ---
    coach_reply: str = ""

    # --- Metadata ---
    user_id: int | None = None
    turn_count: int = 0
