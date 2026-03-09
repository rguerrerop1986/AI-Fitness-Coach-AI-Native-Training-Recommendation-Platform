"""
Shared state for the recommendation LangGraph workflow.
"""
from typing import TypedDict


class RecommendationState(TypedDict, total=False):
    """State passed between recommendation graph nodes."""

    user_id: int
    date: str

    checkin: dict
    recent_workouts: list
    previous_recommendations: list

    exercise_catalog: list

    readiness_score: float
    readiness_flags: list

    recommendation_type: str

    candidate_exercises: list
    recommendation_plan: dict

    validation_errors: list
    warnings: list

    persisted_recommendation_id: int | None
    error: str | None
