"""
LangGraph workflow: load context -> analyze readiness -> route type -> retrieve candidates
-> build recommendation -> validate -> (persist | fallback -> persist) -> END.
Synchronous, request-scoped; no checkpointer.
"""
from langgraph.graph import StateGraph, END

from apps.training.graph.state import RecommendationState
from apps.training.graph import nodes


def _is_valid(state: RecommendationState) -> str:
    """If validation passed, go to persist; else fallback."""
    errors = state.get("validation_errors") or []
    return "persist" if not errors else "fallback"


workflow = StateGraph(RecommendationState)

workflow.add_node("load_user_context", nodes.load_user_context)
workflow.add_node("analyze_readiness", nodes.analyze_readiness)
workflow.add_node("route_recommendation_type", nodes.route_recommendation_type)
workflow.add_node("retrieve_candidate_exercises", nodes.retrieve_candidate_exercises)
workflow.add_node("build_recommendation", nodes.build_recommendation)
workflow.add_node("validate_recommendation", nodes.validate_recommendation)
workflow.add_node("fallback_recommendation", nodes.fallback_recommendation)
workflow.add_node("persist_recommendation", nodes.persist_recommendation)

workflow.set_entry_point("load_user_context")
workflow.add_edge("load_user_context", "analyze_readiness")
workflow.add_edge("analyze_readiness", "route_recommendation_type")
workflow.add_edge("route_recommendation_type", "retrieve_candidate_exercises")
workflow.add_edge("retrieve_candidate_exercises", "build_recommendation")
workflow.add_edge("build_recommendation", "validate_recommendation")
workflow.add_conditional_edges("validate_recommendation", _is_valid, {
    "persist": "persist_recommendation",
    "fallback": "fallback_recommendation",
})
workflow.add_edge("fallback_recommendation", "persist_recommendation")
workflow.add_edge("persist_recommendation", END)

graph = workflow.compile()
