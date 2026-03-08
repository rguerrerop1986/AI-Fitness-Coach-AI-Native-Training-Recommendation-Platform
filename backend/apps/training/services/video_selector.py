"""
Select safe candidate videos based on readiness result and check-in.
Returns 3-5 candidates for the LLM to choose from.

NOTE: The recommendation flow uses apps.training.services.exercise_selector (Exercise from
catalogs) as the source of truth, not this module. This module is kept for backward
compatibility or non-recommendation use only. Do not use get_candidate_videos for
POST /api/training/recommendations/generate/.
"""
from typing import List, Optional

from django.db.models import Q, QuerySet

from apps.training.models import DailyCheckIn, TrainingVideo
from apps.training.services.readiness import ReadinessResult


# Map allowed_intensity to difficulty and category filters
INTENSITY_TO_MAX_DIFFICULTY = {
    "recovery": ["low"],
    "light": ["low", "medium"],
    "moderate": ["low", "medium"],
    "intense": ["low", "medium", "high"],
    "max": ["low", "medium", "high", "max"],
}


def get_candidate_videos(
    readiness: ReadinessResult,
    check_in: Optional[DailyCheckIn],
    limit: int = 5,
) -> List[TrainingVideo]:
    """
    Return a list of 3 to 5 candidate videos safe for the user's current state.
    - Respects allowed_intensity (difficulty cap).
    - If joint pain or high leg soreness, exclude explosive / heavy leg stress.
    - Prefer recovery category when readiness is recovery or light.
    """
    qs = TrainingVideo.objects.filter(is_active=True)
    allowed = readiness.allowed_intensity
    max_difficulties = INTENSITY_TO_MAX_DIFFICULTY.get(allowed, ["low", "medium", "high", "max"])
    qs = qs.filter(difficulty__in=max_difficulties)

    # Joint pain or recovery -> only recovery / low impact
    if allowed == "recovery":
        qs = qs.filter(
            Q(category=TrainingVideo.Category.RECOVERY) | Q(difficulty=TrainingVideo.Difficulty.LOW)
        )

    # High leg soreness or pain: avoid explosive and heavy leg stress
    avoid_explosive_legs = False
    if check_in:
        if check_in.joint_pain:
            avoid_explosive_legs = True
        if (check_in.soreness_legs or 0) >= 6:
            avoid_explosive_legs = True
    if avoid_explosive_legs:
        qs = qs.filter(explosive=False)
        # Optionally reduce heavy leg stress (stresses_legs + high difficulty)
        qs = qs.exclude(
            stresses_legs=True,
            difficulty__in=[TrainingVideo.Difficulty.HIGH, TrainingVideo.Difficulty.MAX],
        )

    # When recovery or light, prefer recovery/cardio balance over max plyo
    if allowed in ("recovery", "light"):
        qs = qs.exclude(
            category=TrainingVideo.Category.PLYOMETRICS,
            difficulty=TrainingVideo.Difficulty.MAX,
        )

    # Order for variety: mix categories, then by difficulty
    qs = qs.order_by("category", "difficulty")[: limit * 2]
    # Return up to `limit` distinct videos (in case ordering produces duplicates)
    seen_pk = set()
    result: List[TrainingVideo] = []
    for v in qs:
        if v.pk not in seen_pk:
            seen_pk.add(v.pk)
            result.append(v)
        if len(result) >= limit:
            break

    return result
