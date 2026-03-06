"""Safety override node — return safety-aware template response."""

from app.ai.state import GraphState


async def handle_safety(state: GraphState) -> dict:
    """Generate a predefined safety response when safety flags are detected.

    TODO: implement keyword + regex pre-check, plus LLM-detected flags from parse.
    """
    return {
        "coach_reply": "我注意到你可能正在经历困难时期。"
        "如果你需要紧急帮助，请联系专业心理援助热线。"
    }
