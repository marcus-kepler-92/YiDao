"""PatternSkill ORM model — stores pattern-based coaching skill configurations."""

from sqlalchemy import Boolean, Column, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB

from app.models.base import BaseModel


class PatternSkill(BaseModel):
    """Pattern Skill 配置表

    每条记录对应一个 (scene, pattern_name) 组合的完整教练技能配置。
    结构化模板和行动库以 JSONB 存储，通过 Admin API 即时修改。
    """

    __tablename__ = "pattern_skills"
    __table_args__ = (
        UniqueConstraint("scene", "pattern_name", name="uq_pattern_skills_scene_pattern"),
    )

    scene = Column(String(50), nullable=False, index=True)
    pattern_name = Column(String(100), nullable=False, index=True)

    situation_template = Column(JSONB, nullable=False, default=list)
    advantages_template = Column(JSONB, nullable=False, default=list)
    blindspots_template = Column(JSONB, nullable=False, default=list)
    actions_library = Column(JSONB, nullable=False, default=list)

    is_active = Column(Boolean, nullable=False, default=True, index=True)
