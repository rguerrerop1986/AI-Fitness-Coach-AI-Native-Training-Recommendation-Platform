"""
Daily recommendation service: rule-based get-or-create for training and diet (fallback path).

This module provides the non-LLM recommendation path used when the AI daily plan is
unavailable or returns no valid output. It is idempotent per (client, date).

  - Recommendation logic: Uses client context (check-ins, training logs, previous
    recommendations, active plan) to derive readiness, fatigue, and yesterday's
    training type. Applies heuristic rules (e.g., high pain/fatigue → recovery;
    low energy → mobility) to choose recommendation_type and intensity, then
    selects exercises or videos from the catalog only.
  - Contextual data usage: build_client_recommendation_context() aggregates
    check-ins, training logs, recent daily recommendations, active plan cycle,
    and catalog counts. This context drives both the rule-based logic here and
    the AI context builder in ai_daily_plan.
  - Diet: Built strictly from catalog Food or from active DietPlan meal items.
  - Training: Built strictly from catalog Exercise (and TrainingVideo); training_group
    and modality are derived and persisted. No free-text or invented exercises.
"""
import logging
from datetime import date, timedelta
from decimal import Decimal
from typing import Any, List, Optional, Tuple

from django.db import transaction
from django.utils import timezone

from apps.clients.models import Client
from apps.plans.models import PlanCycle, DietPlan
from apps.tracking.models import (
    CheckIn,
    TrainingLog,
    DailyTrainingRecommendation,
    DailyTrainingRecommendationExercise,
    DailyDietRecommendation,
    DailyDietRecommendationMeal,
    DailyDietRecommendationMealFood,
    DailyExerciseRecommendation,
)
from apps.catalogs.models import Exercise, Food
from apps.training.models import TrainingVideo
from apps.recommendations.selectors import (
    get_active_plan_cycle_for_client,
    get_recent_training_logs,
    get_recent_daily_recommendations,
    get_exercises_for_recommendation,
)

logger = logging.getLogger(__name__)

# Minimum active foods required to build a daily diet from catalog (no plan)
MIN_FOODS_FOR_DIET = 6

# Minimum active exercises required to build a daily training from catalog (no video)
MIN_EXERCISES_FOR_TRAINING = 2

# Diet recommendation is the same for a 15-day period; training is daily
DIET_PERIOD_DAYS = 15
_DIET_EPOCH = date(2000, 1, 1)


def _diet_period_start(for_date: date) -> date:
    """Return the first day of the 15-day period containing for_date."""
    days_since_epoch = (for_date - _DIET_EPOCH).days
    period_index = days_since_epoch // DIET_PERIOD_DAYS
    return _DIET_EPOCH + timedelta(days=period_index * DIET_PERIOD_DAYS)


class InsufficientCatalogError(Exception):
    """Raised when catalog (foods or exercises) has too few items to build a recommendation."""
    def __init__(self, message: str, catalog: str):
        self.catalog = catalog  # 'foods' or 'exercises'
        super().__init__(message)


def build_client_recommendation_context(
    client: Client,
    target_date: date,
) -> dict[str, Any]:
    """
    Build the shared context package for recommendation logic (Context Builder).

    Aggregates: recent check-ins (tracking.CheckIn), training logs, previous daily
    recommendations (training + diet), yesterday's training, active plan cycle and
    diet/workout plans, and catalog counts (exercises, videos, foods). Used by both
    the rule-based daily_recommendation_service and the AI daily plan context builder
    to ensure consistent contextual data for personalization.
    """
    day_before = target_date - timedelta(days=1)
    week_start = target_date - timedelta(days=14)

    # Checkins (tracking.CheckIn is client-scoped)
    recent_checkins = list(
        CheckIn.objects.filter(
            client=client,
            date__gte=week_start,
            date__lt=target_date,
        ).order_by('-date')[:7]
    )
    today_checkin = next((c for c in recent_checkins if c.date == day_before), None)
    readiness = None
    energy = None
    fatigue = None
    sleep_quality = None
    if today_checkin or recent_checkins:
        c = today_checkin or recent_checkins[0]
        fatigue = c.fatigue
        energy = (10 - (c.fatigue or 0)) if c.fatigue else None
        readiness = 'low' if (c.fatigue or 0) >= 6 else ('high' if (c.fatigue or 0) <= 3 else 'medium')
        # CheckIn doesn't have sleep; use RPE as proxy for recovery
        if c.rpe is not None:
            energy = 10 - c.rpe if energy is None else energy

    # Training logs (last 7 days before target_date)
    recent_logs = list(
        get_recent_training_logs(client, days=7, before_date=target_date)
    )
    last_log = recent_logs[0] if recent_logs else None
    last_pain = last_log.pain_level if last_log else None
    last_energy = last_log.energy_level if last_log else None
    last_rpe = last_log.rpe if last_log else None

    # Previous daily exercise recommendations (for variety)
    recent_recs = get_recent_daily_recommendations(client, days=3, before_date=target_date)
    yesterday_type = None
    if recent_recs and recent_recs[0].date == day_before:
        yesterday_type = recent_recs[0].type

    # Previous daily training recommendations (our new model)
    recent_training_recs = list(
        DailyTrainingRecommendation.objects.filter(
            client=client,
            date__gte=week_start,
            date__lt=target_date,
        ).select_related('recommended_video').prefetch_related('exercises__exercise').order_by('-date')[:3]
    )
    yesterday_training = next((r for r in recent_training_recs if r.date == day_before), None)

    # Active plan cycle
    active_cycle = get_active_plan_cycle_for_client(client, target_date)
    diet_plan = active_cycle.diet_plan if active_cycle else None
    workout_plan = active_cycle.workout_plan if active_cycle else None

    # Catalog counts (for fallbacks)
    exercises_count = Exercise.objects.filter(is_active=True).count()
    videos_count = TrainingVideo.objects.filter(is_active=True).count()

    foods_count = Food.objects.filter(is_active=True).count()
    return {
        'client_id': client.id,
        'target_date': target_date,
        'recent_checkins': recent_checkins,
        'today_checkin': today_checkin,
        'readiness': readiness,
        'energy': energy,
        'fatigue': fatigue,
        'sleep_quality': sleep_quality,
        'recent_training_logs': recent_logs,
        'last_log': last_log,
        'last_pain': last_pain,
        'last_energy': last_energy,
        'last_rpe': last_rpe,
        'recent_daily_recommendations': recent_recs,
        'yesterday_type': yesterday_type,
        'recent_training_recommendations': recent_training_recs,
        'yesterday_training': yesterday_training,
        'active_cycle': active_cycle,
        'diet_plan': diet_plan,
        'workout_plan': workout_plan,
        'exercises_count': exercises_count,
        'videos_count': videos_count,
        'foods_count': foods_count,
        'client_level': (client.level or 'beginner').lower(),
    }


INSANITY_NAME_PATTERNS = [
    'insanity',
    'max interval',
    'pure cardio',
    'cardio recovery',
    'core cardio & balance',
    'plyometric cardio circuit',
    'upper body weight training',
    'max recovery',
    'cardio abs',
]


def _is_insanity_name(name: str | None) -> bool:
    if not name:
        return False
    lower = name.lower()
    return any(pat in lower for pat in INSANITY_NAME_PATTERNS)


def _is_insanity_exercise(ex: Exercise) -> bool:
    tags = [str(t).lower() for t in (ex.tags or [])]
    if 'insanity' in tags:
        return True
    return _is_insanity_name(ex.name)


def _is_active_recovery_exercise(ex: Exercise) -> bool:
    """
    Heurística para reposo activo: cardio suave, máquinas o movilidad.
    Usa muscle_group, equipment_type y tags.
    """
    mg = (ex.muscle_group or '').lower()
    eq = (ex.equipment_type or '').lower()
    tags = [str(t).lower() for t in (ex.tags or [])]
    low_impact_tags = {'low_impact', 'no-impact', 'warmup', 'recovery', 'cooldown'}
    if mg == 'cardio' and (low_impact_tags & set(tags)):
        return True
    if mg == 'cardio' and eq == 'maquina':
        return True
    if 'mobility' in tags or 'movilidad' in tags:
        return True
    return False


def _derive_training_group(
    rec_type: str,
    exercises: List[Exercise],
    prefer_recovery: bool,
) -> str:
    """
    Derive training_group from recommendation type and exercise list.
    Returns choice value: upper_body, lower_body, core, insanity, full_body, active_recovery.
    """
    if prefer_recovery or rec_type == DailyTrainingRecommendation.RecommendationType.RECOVERY:
        # Si todos los ejercicios son cardio suave / movilidad, usar reposo activo
        if exercises and all(_is_active_recovery_exercise(ex) for ex in exercises):
            return DailyTrainingRecommendation.TrainingGroup.ACTIVE_RECOVERY
        # Fallback: reposo activo como tipo global de día
        return DailyTrainingRecommendation.TrainingGroup.ACTIVE_RECOVERY

    if not exercises:
        return DailyTrainingRecommendation.TrainingGroup.FULL_BODY

    # 1) Insanity: por nombre o tags en cualquiera de los ejercicios
    if any(_is_insanity_exercise(ex) for ex in exercises):
        return DailyTrainingRecommendation.TrainingGroup.INSANITY

    # 2) Heurística de grupos musculares principales
    upper_mg = {'shoulders', 'back', 'chest', 'biceps', 'triceps', 'forearms'}
    lower_mg = {'quads', 'hamstrings', 'glutes', 'calves'}
    core_mg = {'core'}

    counts = {'upper': 0, 'lower': 0, 'core': 0}
    has_full_body = False
    has_cardio = False
    has_active_recovery_like = False

    for ex in exercises:
        mg = (ex.muscle_group or '').lower()
        if mg in upper_mg:
            counts['upper'] += 1
        elif mg in lower_mg:
            counts['lower'] += 1
        elif mg in core_mg:
            counts['core'] += 1
        elif mg == 'full_body':
            has_full_body = True
        elif mg == 'cardio':
            has_cardio = True
        if _is_active_recovery_exercise(ex):
            has_active_recovery_like = True

    # 3) Cardio suave / recuperación activa sin fuerza clara
    if has_cardio and has_active_recovery_like and counts['upper'] == 0 and counts['lower'] == 0:
        return DailyTrainingRecommendation.TrainingGroup.ACTIVE_RECOVERY

    # 4) Solo core
    if counts['core'] and counts['upper'] == 0 and counts['lower'] == 0 and not has_full_body:
        return DailyTrainingRecommendation.TrainingGroup.CORE

    # 5) Full body explícito o mezcla fuerte de tren superior e inferior
    if has_full_body or (counts['upper'] and counts['lower']):
        return DailyTrainingRecommendation.TrainingGroup.FULL_BODY

    # 6) Predominio tren superior / inferior
    if counts['upper'] > counts['lower']:
        return DailyTrainingRecommendation.TrainingGroup.UPPER_BODY
    if counts['lower'] > counts['upper']:
        return DailyTrainingRecommendation.TrainingGroup.LOWER_BODY

    # 7) Fallback: full body
    return DailyTrainingRecommendation.TrainingGroup.FULL_BODY


def generate_training_recommendation(
    client: Client,
    target_date: date,
    context: Optional[dict] = None,
) -> DailyTrainingRecommendation:
    """
    Create and persist a daily training recommendation for client on target_date.
    Idempotent: if one already exists, returns it. Otherwise builds from context:
    only catalog exercises (or video). Sets training_group. Raises InsufficientCatalogError
    if no video and not enough exercises.
    """
    existing = (
        DailyTrainingRecommendation.objects.filter(client=client, date=target_date)
        .select_related('recommended_video')
        .prefetch_related('exercises__exercise')
        .first()
    )
    if existing:
        return existing

    ctx = context or build_client_recommendation_context(client, target_date)
    last_pain = ctx.get('last_pain')
    last_energy = ctx.get('last_energy')
    last_rpe = ctx.get('last_rpe')
    fatigue = ctx.get('fatigue')
    yesterday_training = ctx.get('yesterday_training')
    client_level = ctx.get('client_level', 'beginner')
    videos_count = ctx.get('videos_count', 0)
    exercises_count = ctx.get('exercises_count', 0)

    # Decide type and intensity
    rec_type = DailyTrainingRecommendation.RecommendationType.STRENGTH
    prefer_recovery = False
    max_intensity = 6
    rationale_parts = []
    warnings = ''

    if (last_pain is not None and last_pain >= 6) or (fatigue is not None and fatigue >= 6):
        rec_type = DailyTrainingRecommendation.RecommendationType.RECOVERY
        prefer_recovery = True
        max_intensity = 3
        rationale_parts.append('Priorizamos recuperación por fatiga o dolor reciente.')
        warnings = 'Evita esfuerzo máximo. Si el dolor persiste, consulta a tu médico.'
    elif (last_energy is not None and last_energy <= 3) or (last_rpe is not None and last_rpe >= 8):
        rec_type = DailyTrainingRecommendation.RecommendationType.MOBILITY
        max_intensity = 4
        rationale_parts.append('Sesión suave según tu energía reciente.')
    elif yesterday_training and yesterday_training.recommendation_type == rec_type:
        rec_type = DailyTrainingRecommendation.RecommendationType.CARDIO
        rationale_parts.append('Variamos el estímulo respecto a ayer.')

    if not rationale_parts:
        rationale_parts.append('Rutina equilibrada según tu nivel.')

    reasoning_summary = ' '.join(rationale_parts)
    coach_message = 'Enfócate en técnica y control. Hidrátate bien.'
    if prefer_recovery:
        coach_message = 'Día de recuperación activa. Escucha a tu cuerpo.'

    recommended_video = None
    exercises_to_add: list[Tuple[Exercise, int, int, Optional[int], Optional[int], str]] = []

    if prefer_recovery and videos_count > 0:
        video = (
            TrainingVideo.objects.filter(
                is_active=True,
                category=TrainingVideo.Category.RECOVERY,
            ).order_by('?').first()
            or TrainingVideo.objects.filter(is_active=True, difficulty=TrainingVideo.Difficulty.LOW)
            .order_by('?').first()
        )
        if video:
            recommended_video = video
            logger.info('Daily training rec: client=%s date=%s video=%s', client.id, target_date, video.name)

    if not recommended_video and exercises_count > 0:
        from apps.recommendations.services.daily_exercise import exercise_to_type
        difficulty = {'beginner': 'beginner', 'intermediate': 'intermediate', 'advanced': 'advanced'}.get(
            client_level, 'beginner'
        )
        qs = get_exercises_for_recommendation(
            max_intensity=max_intensity,
            tags_any=['mobility', 'low_impact'] if prefer_recovery else None,
        )
        qs = qs.filter(difficulty=difficulty)
        candidates = list(qs[:8])
        exclude_type = yesterday_training.recommendation_type if yesterday_training else None
        for ex in candidates[:4]:
            ex_type = exercise_to_type(ex)
            if exclude_type and getattr(ex_type, 'value', ex_type) == exclude_type:
                continue
            sets = 3 if rec_type == DailyTrainingRecommendation.RecommendationType.STRENGTH else 2
            reps = 12 if rec_type == DailyTrainingRecommendation.RecommendationType.STRENGTH else 10
            exercises_to_add.append((ex, sets, reps, None, 60, ''))
        if not exercises_to_add and candidates:
            ex = candidates[0]
            exercises_to_add.append((ex, 3, 12, None, 60, ''))

    if not recommended_video and not exercises_to_add:
        if exercises_count < MIN_EXERCISES_FOR_TRAINING and videos_count == 0:
            raise InsufficientCatalogError(
                f'No hay suficientes ejercicios en el catálogo (mínimo {MIN_EXERCISES_FOR_TRAINING}). '
                'Contacta a tu coach para dar de alta ejercicios.',
                catalog='exercises',
            )
        if videos_count > 0:
            video = TrainingVideo.objects.filter(is_active=True).order_by('?').first()
            if video:
                recommended_video = video

    training_group = DailyTrainingRecommendation.TrainingGroup.FULL_BODY
    if recommended_video and not exercises_to_add:
        # Clasificar videos tipo Insanity por nombre
        if _is_insanity_name(getattr(recommended_video, 'name', None)) or getattr(
            recommended_video, 'program', ''
        ).lower() == 'insanity':
            training_group = DailyTrainingRecommendation.TrainingGroup.INSANITY
        else:
            training_group = (
                DailyTrainingRecommendation.TrainingGroup.ACTIVE_RECOVERY
                if prefer_recovery
                else DailyTrainingRecommendation.TrainingGroup.FULL_BODY
            )
    elif exercises_to_add:
        training_group = _derive_training_group(
            rec_type,
            [e[0] for e in exercises_to_add],
            prefer_recovery,
        )

    with transaction.atomic():
        rec = DailyTrainingRecommendation.objects.create(
            client=client,
            date=target_date,
            recommendation_type=rec_type,
            training_group=training_group,
            reasoning_summary=reasoning_summary,
            warnings=warnings,
            coach_message=coach_message,
            recommended_video=recommended_video,
        )
        for order, (exercise, sets, reps, duration_minutes, rest_seconds, notes) in enumerate(exercises_to_add, 1):
            DailyTrainingRecommendationExercise.objects.create(
                recommendation=rec,
                exercise=exercise,
                order=order,
                sets=sets,
                reps=reps,
                duration_minutes=duration_minutes,
                rest_seconds=rest_seconds,
                notes=notes or '',
            )
        logger.info(
            'Created DailyTrainingRecommendation id=%s client=%s date=%s video=%s exercises=%s training_group=%s',
            rec.id, client.id, target_date, bool(recommended_video), len(exercises_to_add), training_group,
        )
    return (
        DailyTrainingRecommendation.objects.filter(pk=rec.pk)
        .select_related('recommended_video')
        .prefetch_related('exercises__exercise')
        .get()
    )


def ensure_training_group(rec: DailyTrainingRecommendation) -> DailyTrainingRecommendation:
    """
    Backwards compatibility: derive and persist training_group for older
    DailyTrainingRecommendation rows that lack it.
    """
    if getattr(rec, 'training_group', None):
        return rec

    # Prefer exercises when disponibles
    line_items = list(rec.exercises.select_related('exercise').all())
    exercises: List[Exercise] = [li.exercise for li in line_items if li.exercise]

    if exercises:
        group = _derive_training_group(
            rec.recommendation_type,
            exercises,
            prefer_recovery=(rec.recommendation_type == DailyTrainingRecommendation.RecommendationType.RECOVERY),
        )
    else:
        video = rec.recommended_video
        if video and (_is_insanity_name(video.name) or (video.program or '').lower() == 'insanity'):
            group = DailyTrainingRecommendation.TrainingGroup.INSANITY
        elif video and rec.recommendation_type == DailyTrainingRecommendation.RecommendationType.RECOVERY:
            group = DailyTrainingRecommendation.TrainingGroup.ACTIVE_RECOVERY
        else:
            group = DailyTrainingRecommendation.TrainingGroup.FULL_BODY

    rec.training_group = group
    rec.save(update_fields=['training_group', 'updated_at'])
    return rec


def _meal_type_from_plan(plan_meal_type: str) -> str:
    """Map Plan Meal.MealType to DailyDietRecommendationMeal.MealType."""
    allowed = {'breakfast', 'lunch', 'dinner', 'snack', 'pre_workout', 'post_workout'}
    if plan_meal_type in allowed:
        return plan_meal_type
    return 'snack'


def _build_diet_from_plan(
    diet_plan: DietPlan,
    total_calories: int,
    protein_g: int,
    carbs_g: int,
    fat_g: int,
) -> Tuple[str, str, int, int, int, int, List[Tuple[str, str, List[Tuple[Any, Decimal, str]]]]]:
    """
    Build meal data from active diet plan meals that have real Food items.
    Returns (title, goal, total_calories, protein_g, carbs_g, fat_g, meals_data).
    meals_data: list of (meal_type, meal_title, [(food, quantity, unit), ...]).
    """
    title = diet_plan.title or 'Plan diario personalizado'
    goal = diet_plan.get_goal_display() if diet_plan.goal else 'Mantenimiento'
    meals_with_foods: List[Tuple[str, str, List[Tuple[Any, Decimal, str]]]] = []
    for plan_meal in diet_plan.meals.all().order_by('order')[:6]:
        items = list(plan_meal.items.select_related('food').all())
        if not items:
            continue
        meal_type = _meal_type_from_plan(plan_meal.meal_type)
        meal_title = plan_meal.name or plan_meal.get_meal_type_display()
        food_list = []
        for item in items:
            qty = item.quantity
            unit = 'g'
            food_list.append((item.food, qty, unit))
        meals_with_foods.append((meal_type, meal_title, food_list))
    if not meals_with_foods:
        return title, goal, total_calories, protein_g, carbs_g, fat_g, []
    return title, goal, total_calories, protein_g, carbs_g, fat_g, meals_with_foods


def _build_diet_from_catalog(
    foods_count: int,
) -> Tuple[str, str, int, int, int, int, List[Tuple[str, str, List[Tuple[Any, Decimal, str]]]]]:
    """
    Build meal data from catalog Food only. Requires at least MIN_FOODS_FOR_DIET.
    Returns (title, goal, total_calories, protein_g, carbs_g, fat_g, meals_data).
    """
    if foods_count < MIN_FOODS_FOR_DIET:
        raise InsufficientCatalogError(
            f'No hay suficientes alimentos en el catálogo (mínimo {MIN_FOODS_FOR_DIET}). '
            'Contacta a tu coach para dar de alta alimentos.',
            catalog='foods',
        )
    title = 'Plan diario personalizado'
    goal = 'Mantenimiento'
    total_calories = 1800
    protein_g = 120
    carbs_g = 180
    fat_g = 60
    # Select active foods with variety (by nutritional_group if available)
    all_foods = list(Food.objects.filter(is_active=True).order_by('?')[:24])
    per_meal = max(2, len(all_foods) // 3)
    meals_spec = [
        ('breakfast', 'Desayuno'),
        ('lunch', 'Comida'),
        ('dinner', 'Cena'),
    ]
    meals_with_foods: List[Tuple[str, str, List[Tuple[Any, Decimal, str]]]] = []
    offset = 0
    for meal_type, meal_title in meals_spec:
        chunk = all_foods[offset:offset + per_meal] or all_foods[offset:offset + 1]
        offset += len(chunk)
        if not chunk:
            break
        food_list = []
        for f in chunk:
            # Default quantity: 100g or 1 piece for small counts
            qty = Decimal('100')
            unit = 'g'
            food_list.append((f, qty, unit))
        meals_with_foods.append((meal_type, meal_title, food_list))
    return title, goal, total_calories, protein_g, carbs_g, fat_g, meals_with_foods


def generate_diet_recommendation(
    client: Client,
    target_date: date,
    context: Optional[dict] = None,
) -> DailyDietRecommendation:
    """
    Create and persist a daily diet recommendation using only catalog Food
    (or from active DietPlan meal items when present). Never uses placeholder text.
    Raises InsufficientCatalogError if catalog has too few foods and plan has no items.
    """
    existing = (
        DailyDietRecommendation.objects.filter(client=client, date=target_date)
        .prefetch_related('meals__meal_foods__food')
        .first()
    )
    if existing:
        return existing

    ctx = context or build_client_recommendation_context(client, target_date)
    diet_plan = ctx.get('diet_plan')
    active_cycle = ctx.get('active_cycle')
    foods_count = ctx.get('foods_count', 0)

    coach_message = 'Mantén hidratación y distribuye proteína durante el día.'
    reasoning_summary = 'Plan generado según tu contexto reciente.'
    total_calories = 1800
    protein_g = 120
    carbs_g = 180
    fat_g = 60
    meals_with_foods: List[Tuple[str, str, List[Tuple[Any, Decimal, str]]]] = []
    title = 'Plan diario personalizado'
    goal = 'Mantenimiento'

    if diet_plan and active_cycle:
        if diet_plan.daily_calories:
            total_calories = int(diet_plan.daily_calories)
        if diet_plan.protein_pct and diet_plan.daily_calories:
            protein_g = int((float(diet_plan.daily_calories) * float(diet_plan.protein_pct) / 100) / 4)
        if diet_plan.carbs_pct and diet_plan.daily_calories:
            carbs_g = int((float(diet_plan.daily_calories) * float(diet_plan.carbs_pct) / 100) / 4)
        if diet_plan.fat_pct and diet_plan.daily_calories:
            fat_g = int((float(diet_plan.daily_calories) * float(diet_plan.fat_pct) / 100) / 9)
        title, goal, total_calories, protein_g, carbs_g, fat_g, meals_with_foods = _build_diet_from_plan(
            diet_plan, total_calories, protein_g, carbs_g, fat_g,
        )

    if not meals_with_foods:
        title, goal, total_calories, protein_g, carbs_g, fat_g, meals_with_foods = _build_diet_from_catalog(
            foods_count,
        )

    with transaction.atomic():
        rec = DailyDietRecommendation.objects.create(
            client=client,
            date=target_date,
            title=title,
            goal=goal,
            coach_message=coach_message,
            reasoning_summary=reasoning_summary,
            total_calories=total_calories,
            protein_g=protein_g,
            carbs_g=carbs_g,
            fat_g=fat_g,
        )
        for order, (meal_type, meal_title, food_list) in enumerate(meals_with_foods, 1):
            mt = _meal_type_from_plan(meal_type)
            meal_cal = None
            meal_p = meal_c = meal_f = None
            meal_obj = DailyDietRecommendationMeal.objects.create(
                recommendation=rec,
                meal_type=mt,
                title=meal_title,
                description='',
                calories=meal_cal,
                protein_g=meal_p,
                carbs_g=meal_c,
                fat_g=meal_f,
                order=order,
            )
            for idx, (food, quantity, unit) in enumerate(food_list):
                DailyDietRecommendationMealFood.objects.create(
                    meal=meal_obj,
                    food=food,
                    quantity=quantity,
                    unit=unit,
                    order=idx + 1,
                )
        logger.info(
            'Created DailyDietRecommendation id=%s client=%s date=%s meals=%s',
            rec.id, client.id, target_date, len(meals_with_foods),
        )

    return (
        DailyDietRecommendation.objects.filter(pk=rec.pk)
        .prefetch_related('meals__meal_foods__food')
        .get()
    )


def get_or_create_daily_recommendation(
    client: Client,
    target_date: Optional[date] = None,
) -> Tuple[Optional[DailyTrainingRecommendation], Optional[DailyDietRecommendation]]:
    """
    Get or create both training and diet recommendations for the given client and date.
    Returns (training_rec, diet_rec). Either can be None if generation failed (e.g. no catalog).
    """
    target_date = target_date or timezone.localdate()
    context = build_client_recommendation_context(client, target_date)

    # Training: one recommendation per day (updates daily)
    # Diet: one recommendation per 15-day period (same diet for the whole period)
    diet_date = _diet_period_start(target_date)

    training_rec = None
    diet_rec = None
    try:
        training_rec = generate_training_recommendation(client, target_date, context=context)
    except InsufficientCatalogError:
        raise
    except Exception as e:
        logger.warning('Failed to generate training recommendation: %s', e, exc_info=True)
    try:
        diet_rec = generate_diet_recommendation(client, diet_date, context=context)
    except InsufficientCatalogError:
        raise
    except Exception as e:
        logger.warning('Failed to generate diet recommendation: %s', e, exc_info=True)

    return training_rec, diet_rec
