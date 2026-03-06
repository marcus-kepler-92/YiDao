"""Data access layer for Pattern Skills."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pattern_skill import PatternSkill
from app.schemas.pattern_skill import PatternSkillCreate, PatternSkillUpdate


class PatternSkillRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add(self, data: PatternSkillCreate) -> PatternSkill:
        skill = PatternSkill(**data.model_dump())
        self.db.add(skill)
        await self.db.flush()
        await self.db.refresh(skill)
        return skill

    async def find_by_scene_and_pattern(self, scene: str, pattern_name: str) -> PatternSkill | None:
        query = select(PatternSkill).where(
            PatternSkill.scene == scene,
            PatternSkill.pattern_name == pattern_name,
            PatternSkill.deleted_at.is_(None),
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def find_all(self, active_only: bool = True) -> list[PatternSkill]:
        query = select(PatternSkill).where(PatternSkill.deleted_at.is_(None))
        if active_only:
            query = query.where(PatternSkill.is_active.is_(True))
        query = query.order_by(PatternSkill.scene, PatternSkill.pattern_name)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_by_scene_and_pattern(
        self, scene: str, pattern_name: str, data: PatternSkillUpdate
    ) -> PatternSkill | None:
        skill = await self.find_by_scene_and_pattern(scene, pattern_name)
        if skill is None:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(skill, key, value)
        await self.db.flush()
        await self.db.refresh(skill)
        return skill

    async def remove_by_scene_and_pattern(
        self, scene: str, pattern_name: str
    ) -> PatternSkill | None:
        """Soft-disable: sets is_active = False."""
        skill = await self.find_by_scene_and_pattern(scene, pattern_name)
        if skill is None:
            return None
        skill.is_active = False
        await self.db.flush()
        await self.db.refresh(skill)
        return skill
