"""
Daily exercise recommendation V1: heuristic engine for client portal.
Generates one recommendation per client per day; persists in DailyExerciseRecommendation.
Cold start: uses catalog by level when no logs. Safety: pain/energy gates.
"""
from datetime import date, timedelta
from typing import Any, Optional

from apps.clients.models import Client
from apps.catalogs.models import Exercise
from apps.tracking.models import TrainingLog, DailyExerciseRecommendation
from apps.recommendations.selectors import (
    get_recent_training_logs,
    get_last_log,
    get_recent_daily_recommendations,
    get_exercises_for_recommendation,
)

# Map client level (DB value) to catalog difficulty
LEVEL_TO_DIFFICULTY = {
    'beginner': 'beginner',
    'intermediate': 'intermediate',
    'advanced': 'advanced',
}

# Intensity 1-10 -> our enum
def _intensity_to_enum(val: int) -> str:
    if val <= 3:
        return DailyExerciseRecommendation.Intensity.LOW
    if val <= 6:
        return DailyExerciseRecommendation.Intensity.MODERATE
    return DailyExerciseRecommendation.Intensity.HIGH


def exercise_to_type(exercise: Exercise) -> str:
    """Derive recommendation type from exercise tags and muscle_group. Returns choice value (e.g. 'mobility')."""
    tags = exercise.tags or []
    tag_lower = [ str(t).lower() for t in tags ]
    if 'mobility' in tag_lower or 'movilidad' in tag_lower:
        return DailyExerciseRecommendation.Type.MOBILITY
    if 'hiit' in tag_lower:
        return DailyExerciseRecommendation.Type.HIIT
    if 'cardio' in tag_lower:
        return DailyExerciseRecommendation.Type.CARDIO
    if 'core' in tag_lower:
        return DailyExerciseRecommendation.Type.CORE
    if exercise.muscle_group == 'core':
        return DailyExerciseRecommendation.Type.CORE
    if exercise.muscle_group == 'cardio':
        return DailyExerciseRecommendation.Type.CARDIO
    return DailyExerciseRecommendation.Type.STRENGTH


def generate_daily_recommendation(
    client: Client,
    for_date: Optional[date] = None,
) -> DailyExerciseRecommendation:
    """
    Get or create the daily exercise recommendation for this client and date.
    Uses heuristics: pain gate, energy/RPE gate, level, variety (no same type 2 days in a row).
    Cold start: no logs -> moderate by level from catalog.
    """
    for_date = for_date or date.today()
    existing = DailyExerciseRecommendation.objects.filter(
        client=client,
        date=for_date,
    ).select_related('exercise').first()
    if existing:
        return existing

    level = (client.level or 'beginner').lower()
    difficulty = LEVEL_TO_DIFFICULTY.get(level, 'beginner')

    # Recent logs (before for_date)
    logs = list(
        get_recent_training_logs(client, days=7, before_date=for_date)
    )
    last_log = get_last_log(logs)
    recent_recs = get_recent_daily_recommendations(client, days=3, before_date=for_date)
    yesterday_type: Optional[str] = None
    if recent_recs and recent_recs[0].date == for_date - timedelta(days=1):
        yesterday_type = recent_recs[0].type

    # --- Safety & fatigue gates ---
    max_intensity_num: Optional[int] = None  # 1-10
    tags_any: Optional[list[str]] = None
    rationale_parts: list[str] = []
    metadata: dict[str, Any] = {'last_log_ids': [], 'applied_rules': []}

    if last_log:
        metadata['last_log_ids'] = [last_log.id]
        pain = last_log.pain_level if last_log.pain_level is not None else 0
        energy = last_log.energy_level if last_log.energy_level is not None else 10
        rpe = last_log.rpe if last_log.rpe is not None else 0

        # A) Safety: pain >= 7 -> mobility/low, "descanso activo"
        if pain >= 7:
            tags_any = ['mobility', 'low_impact', 'no-impact']
            max_intensity_num = 3
            rationale_parts.append(
                'Por tu registro reciente de dolor elevado, te recomendamos movilidad o descanso activo.'
            )
            metadata['applied_rules'].append('pain_high_mobility')
        # B) pain 4-6 -> avoid HIIT; moderate, no impact
        elif pain >= 4:
            tags_any = ['mobility', 'low_impact', 'core']
            if max_intensity_num is None:
                max_intensity_num = 5
            rationale_parts.append(
                'Te sugerimos evitar impacto; priorizamos movilidad o core suave.'
            )
            metadata['applied_rules'].append('pain_moderate_no_hiit')

        # C) Fatigue: rpe >= 8 or energy <= 3 -> low/moderate today
        if pain < 7 and (rpe >= 8 or energy <= 3):
            if max_intensity_num is None or max_intensity_num > 4:
                max_intensity_num = min(max_intensity_num or 10, 4)
            if not rationale_parts:
                rationale_parts.append(
                    'Ayer reportaste mucha fatiga o poca energía; hoy una sesión más suave.'
                )
            metadata['applied_rules'].append('fatigue_reduce_intensity')

    # D) Variety: don't repeat same type 2 days in a row (if we have alternatives)
    exclude_type = yesterday_type

    # E) Cold start or default rationale
    if not rationale_parts:
        rationale_parts.append(
            'Rutina equilibrada según tu nivel. ¡Vamos!'
        )
        metadata['applied_rules'].append('default_by_level')

    # --- Pick exercise from catalog ---
    # Use existing selector but filter by difficulty (level)
    qs = Exercise.objects.filter(is_active=True, difficulty=difficulty)
    if max_intensity_num is not None:
        qs = qs.filter(intensity__lte=max_intensity_num)
    if tags_any:
        from django.db.models import Q
        tag_filter = Q()
        for tag in tags_any:
            tag_filter |= Q(tags__contains=[tag])
        qs = qs.filter(tag_filter)
    qs = qs.order_by('?')

    # Apply variety: skip exercises whose type equals yesterday_type
    candidates = list(qs[:20])
    exercise = None
    for ex in candidates:
        ex_type = exercise_to_type(ex)
        ex_type_val = getattr(ex_type, 'value', ex_type)
        if exclude_type and ex_type_val == exclude_type:
            continue
        exercise = ex
        break
    if not exercise and candidates:
        exercise = candidates[0]

    # If no candidates with tags, fallback: any exercise by level
    if not exercise:
        qs_fallback = Exercise.objects.filter(
            is_active=True,
            difficulty=difficulty,
        )
        if max_intensity_num is not None:
            qs_fallback = qs_fallback.filter(intensity__lte=max_intensity_num)
        exercise = qs_fallback.order_by('?').first()

    # Build recommendation
    intensity_enum = DailyExerciseRecommendation.Intensity.MODERATE
    type_enum = DailyExerciseRecommendation.Type.STRENGTH
    if exercise:
        intensity_enum = _intensity_to_enum(exercise.intensity)
        type_enum = exercise_to_type(exercise)  # returns enum; model stores .value
    else:
        rationale_parts.append(
            'No hay ejercicios en el catálogo para tu nivel hoy. Pide a tu coach que agregue ejercicios base.'
        )

    rationale = ' '.join(rationale_parts)
    rec = DailyExerciseRecommendation.objects.create(
        client=client,
        date=for_date,
        exercise=exercise,
        intensity=intensity_enum,
        type=type_enum,
        rationale=rationale,
        status=DailyExerciseRecommendation.Status.RECOMMENDED,
        metadata=metadata,
    )
    return rec
