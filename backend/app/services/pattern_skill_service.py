"""Business logic for Pattern Skill management."""

from app.exceptions.base import NotFoundException
from app.models.pattern_skill import PatternSkill
from app.repository.pattern_skill_repository import PatternSkillRepository
from app.schemas.pattern_skill import PatternSkillCreate, PatternSkillUpdate


class PatternSkillService:
    def __init__(self, repo: PatternSkillRepository):
        self.repo = repo

    async def create(self, data: PatternSkillCreate) -> PatternSkill:
        existing = await self.repo.find_by_scene_and_pattern(data.scene, data.pattern_name)
        if existing:
            raise ValueError(
                f"Pattern skill already exists: scene={data.scene}, pattern={data.pattern_name}"
            )
        return await self.repo.add(data)

    async def get_by_scene_and_pattern(self, scene: str, pattern_name: str) -> PatternSkill:
        skill = await self.repo.find_by_scene_and_pattern(scene, pattern_name)
        if skill is None:
            raise NotFoundException(f"Pattern skill not found: {scene}/{pattern_name}")
        return skill

    async def list_all(self, active_only: bool = True) -> list[PatternSkill]:
        return await self.repo.find_all(active_only=active_only)

    async def update(self, scene: str, pattern_name: str, data: PatternSkillUpdate) -> PatternSkill:
        skill = await self.repo.update_by_scene_and_pattern(scene, pattern_name, data)
        if skill is None:
            raise NotFoundException(f"Pattern skill not found: {scene}/{pattern_name}")
        return skill

    async def disable(self, scene: str, pattern_name: str) -> PatternSkill:
        skill = await self.repo.remove_by_scene_and_pattern(scene, pattern_name)
        if skill is None:
            raise NotFoundException(f"Pattern skill not found: {scene}/{pattern_name}")
        return skill
