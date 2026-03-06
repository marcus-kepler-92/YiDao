"""Render node — format the final reply for the API response."""

from app.ai.state import GraphState


async def render_reply(state: GraphState) -> dict:
    """Compose the response payload for the API layer.

    TODO: format structured coach output or clarification reply.
    """
    return {}
