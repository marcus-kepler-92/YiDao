"""
LangGraph graph definition — the main conversation processing pipeline.

This is a placeholder that defines the graph skeleton.
Individual node implementations live in app/ai/nodes/.
"""

from langgraph.graph import END, StateGraph

from app.ai.nodes.bucket_update import update_bucket
from app.ai.nodes.case_manager import select_bucket
from app.ai.nodes.coach_agent import generate_coaching
from app.ai.nodes.parse_agent import parse_message
from app.ai.nodes.pattern_skill import load_pattern_skill
from app.ai.nodes.render import render_reply
from app.ai.nodes.safety import handle_safety
from app.ai.state import BucketStage, GraphState


def _route_after_update(state: GraphState) -> str:
    """Conditional edge: decide next node based on bucket stage + safety."""
    if state.safety_flags:
        return "handle_safety"
    if state.stage in (BucketStage.COLLECTING, BucketStage.FOCUSING):
        return "render_reply"
    if state.stage in (BucketStage.COACHING_PROBE, BucketStage.COACHING_DEEP):
        return "load_pattern_skill"
    return "render_reply"


def build_graph() -> StateGraph:
    """Construct and return the compiled conversation graph."""
    graph = StateGraph(GraphState)

    graph.add_node("parse_message", parse_message)
    graph.add_node("select_bucket", select_bucket)
    graph.add_node("update_bucket", update_bucket)
    graph.add_node("handle_safety", handle_safety)
    graph.add_node("load_pattern_skill", load_pattern_skill)
    graph.add_node("generate_coaching", generate_coaching)
    graph.add_node("render_reply", render_reply)

    graph.set_entry_point("parse_message")
    graph.add_edge("parse_message", "select_bucket")
    graph.add_edge("select_bucket", "update_bucket")
    graph.add_conditional_edges("update_bucket", _route_after_update)
    graph.add_edge("handle_safety", "render_reply")
    graph.add_edge("load_pattern_skill", "generate_coaching")
    graph.add_edge("generate_coaching", "render_reply")
    graph.add_edge("render_reply", END)

    return graph
