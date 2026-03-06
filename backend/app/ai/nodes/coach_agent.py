"""Coach Agent node — generate structured coaching response."""

from app.ai.state import GraphState


async def generate_coaching(state: GraphState) -> dict:
    """Produce the structured coaching reply (situation, advantages, blindspots, actions).

    TODO: implement LLM call using pattern skill data + prompt from Langfuse.
    """
    return {}
