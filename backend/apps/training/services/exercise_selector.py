"""
Select safe candidate exercises from catalogs.Exercise based on readiness and check-in.
Returns 3-5 candidates for the LLM. This is the source of truth (replaces TrainingVideo for recommendations).
"""
from typing import List, Optional

from django.db.models import Q, QuerySet

from apps.catalogs.models import Exercise
from apps.training.models import DailyCheckIn
from apps.training.services.readiness import ReadinessResult

# Map allowed_intensity to max exercise intensity (1-10)
INTENSITY_TO_MAX_LEVEL = {
    "recovery": 3,
    "light": 5,
    "moderate": 7,
    "intense": 8,
    "max": 10,
}

LOWER_BODY_GROUPS = {"quads", "hamstrings", "glutes", "calves"}


def get_candidate_exercises(
    readiness: ReadinessResult,
    check_in: Optional[DailyCheckIn],
    limit: int = 5,
) -> List[Exercise]:
    """
    Return 3-5 candidate exercises from catalogs.Exercise safe for the user's current state.
    - Respects allowed_intensity (caps exercise intensity).
    - If joint pain or high leg soreness, exclude high-intensity lower body and hiit/explosive tags.
    - When recovery/light, prefer low_impact / mobility tags.
    """
    qs = Exercise.objects.filter(is_active=True)
    allowed = readiness.allowed_intensity
    max_intensity = INTENSITY_TO_MAX_LEVEL.get(allowed, 10)
    qs = qs.filter(intensity__lte=max_intensity)

    # Recovery: only low intensity or low_impact/mobility
    if allowed == "recovery":
        qs = qs.filter(intensity__lte=3)

    # Joint pain or high leg soreness: avoid explosive / heavy lower body
    avoid_explosive_legs = False
    if check_in:
        if check_in.joint_pain:
            avoid_explosive_legs = True
        if (check_in.soreness_legs or 0) >= 6:
            avoid_explosive_legs = True

    if avoid_explosive_legs:
        # Exclude high-intensity lower body (no tags in DB for hiit/explosive in all backends)
        qs = qs.exclude(
            muscle_group__in=list(LOWER_BODY_GROUPS),
            intensity__gte=7,
        )

    # wants_intensity False => user prefers recovery/light; cap intensity
    if check_in and getattr(check_in, "wants_intensity", True) is False:
        qs = qs.filter(intensity__lte=5)

    qs = qs.order_by("intensity", "muscle_group", "name")[: limit * 2]
    seen_pk = set()
    result: List[Exercise] = []
    for ex in qs:
        if ex.pk not in seen_pk:
            seen_pk.add(ex.pk)
            result.append(ex)
        if len(result) >= limit:
            break
    return result
