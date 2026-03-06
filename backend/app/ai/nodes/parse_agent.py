"""Parse Agent node — extracts intent, slots, and safety flags from user message."""

from app.ai.state import GraphState


async def parse_message(state: GraphState) -> dict:
    """Analyse the user message and return structured parse results.

    TODO: implement LLM call with structured output (Pydantic model).
    """
    return {}
