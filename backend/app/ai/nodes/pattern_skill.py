"""Pattern Skill node — load the matching skill config from DB."""

from app.ai.state import GraphState


async def load_pattern_skill(state: GraphState) -> dict:
    """Fetch pattern skill data from pattern_skills DB table.

    TODO: query PatternSkillRepository by (scene, pattern_name).
    """
    return {}
