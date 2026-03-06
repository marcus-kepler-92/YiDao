"""CaseManager node — select or create the appropriate bucket."""

from app.ai.state import GraphState


async def select_bucket(state: GraphState) -> dict:
    """Determine which bucket the current message belongs to.

    TODO: query existing buckets' meta_summary, let LLM decide assignment.
    """
    return {}
