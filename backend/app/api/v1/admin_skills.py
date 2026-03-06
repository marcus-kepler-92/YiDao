"""Admin API for Pattern Skills CRUD management."""

from fastapi import APIRouter, Depends

from app.dependencies import get_current_active_user, get_pattern_skill_service
from app.models.user import User
from app.schemas.common import Response
from app.schemas.pattern_skill import (
    PatternSkillCreate,
    PatternSkillResponse,
    PatternSkillUpdate,
)
from app.services.pattern_skill_service import PatternSkillService

router = APIRouter(prefix="/admin/skills", tags=["admin-skills"])


@router.get("", response_model=Response[list[PatternSkillResponse]])
async def get_skill_list(
    active_only: bool = True,
    service: PatternSkillService = Depends(get_pattern_skill_service),
    _current_user: User = Depends(get_current_active_user),
):
    skills = await service.list_all(active_only=active_only)
    return Response(data=skills)


@router.get("/{scene}/{pattern_name}", response_model=Response[PatternSkillResponse])
async def get_skill_detail(
    scene: str,
    pattern_name: str,
    service: PatternSkillService = Depends(get_pattern_skill_service),
    _current_user: User = Depends(get_current_active_user),
):
    skill = await service.get_by_scene_and_pattern(scene, pattern_name)
    return Response(data=skill)


@router.post("", response_model=Response[PatternSkillResponse], status_code=201)
async def add_skill(
    data: PatternSkillCreate,
    service: PatternSkillService = Depends(get_pattern_skill_service),
    _current_user: User = Depends(get_current_active_user),
):
    skill = await service.create(data)
    return Response(data=skill)


@router.put("/{scene}/{pattern_name}", response_model=Response[PatternSkillResponse])
async def update_skill_by_scene_pattern(
    scene: str,
    pattern_name: str,
    data: PatternSkillUpdate,
    service: PatternSkillService = Depends(get_pattern_skill_service),
    _current_user: User = Depends(get_current_active_user),
):
    skill = await service.update(scene, pattern_name, data)
    return Response(data=skill)


@router.delete("/{scene}/{pattern_name}", response_model=Response[PatternSkillResponse])
async def remove_skill_by_scene_pattern(
    scene: str,
    pattern_name: str,
    service: PatternSkillService = Depends(get_pattern_skill_service),
    _current_user: User = Depends(get_current_active_user),
):
    skill = await service.disable(scene, pattern_name)
    return Response(data=skill)
