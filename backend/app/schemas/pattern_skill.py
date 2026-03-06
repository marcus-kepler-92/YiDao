"""Pydantic schemas for Pattern Skill Admin API."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PatternSkillBase(BaseModel):
    """Shared fields for Pattern Skill schemas."""

    scene: str = Field(..., max_length=50, description="场景 (work/relationship/family/...)")
    pattern_name: str = Field(..., max_length=100, description="卦簇名称")
    situation_template: list[str] = Field(default_factory=list, description="局面解读模板")
    advantages_template: list[str] = Field(default_factory=list, description="优势模板")
    blindspots_template: list[str] = Field(default_factory=list, description="盲点模板")
    actions_library: list[dict[str, Any]] = Field(default_factory=list, description="行动建议库")


class PatternSkillCreate(PatternSkillBase):
    """Schema for creating a Pattern Skill."""

    pass


class PatternSkillUpdate(BaseModel):
    """Schema for updating a Pattern Skill (all fields optional)."""

    situation_template: list[str] | None = None
    advantages_template: list[str] | None = None
    blindspots_template: list[str] | None = None
    actions_library: list[dict[str, Any]] | None = None
    is_active: bool | None = None


class PatternSkillResponse(PatternSkillBase):
    """Schema for Pattern Skill API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
