"""
Daily recommendation service: get-or-create training and diet recommendations for the client dashboard.
Idempotent per (client, date). Uses catalog exercises/videos and client context (checkins, logs, plan).
"""
import logging
from datetime import date, timedelta
from typing import Any, Optional, Tuple

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
    DailyExerciseRecommendation,
)
from apps.catalogs.models import Exercise
from apps.training.models import TrainingVideo
from apps.recommendations.selectors import (
    get_active_plan_cycle_for_client,
    get_recent_training_logs,
    get_recent_daily_recommendations,
    get_exercises_for_recommendation,
)

logger = logging.getLogger(__name__)


def build_client_recommendation_context(
    client: Client,
    target_date: date,
) -> dict[str, Any]:
    """
    Build a context dict with everything needed to personalize today's recommendation.
    Includes: checkins, readiness/fatigue, feedbacks, recent recommendations, training logs,
    active plan, constraints, and available catalog (exercises, videos).
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
        'client_level': (client.level or 'beginner').lower(),
    }


def generate_training_recommendation(
    client: Client,
    target_date: date,
    context: Optional[dict] = None,
) -> DailyTrainingRecommendation:
    """
    Create and persist a daily training recommendation for client on target_date.
    Idempotent: if one already exists, returns it. Otherwise builds from context:
    favors recovery/light when fatigue high; uses video or exercises from catalog.
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
        # Slight variation: if yesterday was strength, today could be cardio or mobility
        rec_type = DailyTrainingRecommendation.RecommendationType.CARDIO
        rationale_parts.append('Variamos el estímulo respecto a ayer.')

    if not rationale_parts:
        rationale_parts.append('Rutina equilibrada según tu nivel.')

    reasoning_summary = ' '.join(rationale_parts)
    coach_message = 'Enfócate en técnica y control. Hidrátate bien.'
    if prefer_recovery:
        coach_message = 'Día de recuperación activa. Escucha a tu cuerpo.'

    # Choose video or exercises
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
        for i, ex in enumerate(candidates[:4]):
            ex_type = exercise_to_type(ex)
            if exclude_type and getattr(ex_type, 'value', ex_type) == exclude_type:
                continue
            sets = 3 if rec_type == DailyTrainingRecommendation.RecommendationType.STRENGTH else 2
            reps = 12 if rec_type == DailyTrainingRecommendation.RecommendationType.STRENGTH else 10
            exercises_to_add.append((ex, sets, reps, None, 60, ''))
        if not exercises_to_add and candidates:
            ex = candidates[0]
            exercises_to_add.append((ex, 3, 12, None, 60, ''))

    elif not recommended_video and videos_count > 0:
        video = TrainingVideo.objects.filter(is_active=True).order_by('?').first()
        if video:
            recommended_video = video

    with transaction.atomic():
        rec = DailyTrainingRecommendation.objects.create(
            client=client,
            date=target_date,
            recommendation_type=rec_type,
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
            'Created DailyTrainingRecommendation id=%s client=%s date=%s video=%s exercises=%s',
            rec.id, client.id, target_date, bool(recommended_video), len(exercises_to_add),
        )
    # Refetch with prefetch for response
    return (
        DailyTrainingRecommendation.objects.filter(pk=rec.pk)
        .select_related('recommended_video')
        .prefetch_related('exercises__exercise')
        .get()
    )


def generate_diet_recommendation(
    client: Client,
    target_date: date,
    context: Optional[dict] = None,
) -> DailyDietRecommendation:
    """
    Create and persist a daily diet recommendation for client on target_date.
    Idempotent. If active plan with diet_plan exists, derive daily view from it;
    otherwise create a safe default recommendation.
    """
    existing = (
        DailyDietRecommendation.objects.filter(client=client, date=target_date)
        .prefetch_related('meals')
        .first()
    )
    if existing:
        return existing

    ctx = context or build_client_recommendation_context(client, target_date)
    diet_plan = ctx.get('diet_plan')
    active_cycle = ctx.get('active_cycle')

    title = 'Plan diario personalizado'
    goal = 'Mantenimiento'
    coach_message = 'Mantén hidratación y distribuye proteína durante el día.'
    reasoning_summary = 'Plan generado según tu contexto reciente.'
    total_calories = 1800
    protein_g = 120
    carbs_g = 180
    fat_g = 60
    meals_data: list[Tuple[str, str, str, Optional[int], int, int, int]] = []

    if diet_plan and active_cycle:
        title = diet_plan.title or title
        goal = diet_plan.get_goal_display() if diet_plan.goal else goal
        total_calories = diet_plan.daily_calories or total_calories
        if diet_plan.protein_pct and diet_plan.daily_calories:
            protein_g = int((diet_plan.daily_calories * float(diet_plan.protein_pct) / 100) / 4)
        if diet_plan.carbs_pct and diet_plan.daily_calories:
            carbs_g = int((diet_plan.daily_calories * float(diet_plan.carbs_pct) / 100) / 4)
        if diet_plan.fat_pct and diet_plan.daily_calories:
            fat_g = int((diet_plan.daily_calories * float(diet_plan.fat_pct) / 100) / 9)
        for meal in diet_plan.meals.all().order_by('order')[:6]:
            meal_type = meal.meal_type
            meal_title = meal.name or meal.get_meal_type_display()
            desc = meal.description or ''
            cal = None
            for item in meal.items.all():
                try:
                    cal = (cal or 0) + int(item.total_calories or 0)
                except (TypeError, ValueError):
                    pass
            meals_data.append((meal_type, meal_title, desc, cal, 0, 0, 0))
        if not meals_data:
            meals_data = [
                ('breakfast', 'Desayuno', 'Incluye proteína y carbohidratos (ej. huevos, avena, fruta)', 450, 25, 50, 15),
                ('lunch', 'Comida', 'Comida principal equilibrada', 600, 35, 60, 20),
                ('dinner', 'Cena', 'Cena ligera', 450, 30, 45, 15),
            ]
    else:
        meals_data = [
            ('breakfast', 'Desayuno alto en proteína', 'Huevos, avena y fruta', 450, 25, 50, 15),
            ('lunch', 'Comida principal', 'Proteína, vegetales y carbohidratos', 600, 35, 60, 20),
            ('dinner', 'Cena', 'Proteína y vegetales', 450, 30, 45, 15),
        ]

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
        for order, (meal_type, meal_title, desc, cal, p, c, f) in enumerate(meals_data, 1):
            # Map meal_type to our enum (breakfast, lunch, dinner, snack)
            mt = meal_type if meal_type in ('breakfast', 'lunch', 'dinner', 'snack',
                                           'pre_workout', 'post_workout') else 'snack'
            if mt not in ('breakfast', 'lunch', 'dinner', 'snack', 'pre_workout', 'post_workout'):
                mt = 'snack'
            DailyDietRecommendationMeal.objects.create(
                recommendation=rec,
                meal_type=mt,
                title=meal_title,
                description=desc,
                calories=cal,
                protein_g=p or None,
                carbs_g=c or None,
                fat_g=f or None,
                order=order,
            )
        logger.info('Created DailyDietRecommendation id=%s client=%s date=%s', rec.id, client.id, target_date)

    return (
        DailyDietRecommendation.objects.filter(pk=rec.pk)
        .prefetch_related('meals')
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

    training_rec = None
    diet_rec = None
    try:
        training_rec = generate_training_recommendation(client, target_date, context=context)
    except Exception as e:
        logger.warning('Failed to generate training recommendation: %s', e, exc_info=True)
    try:
        diet_rec = generate_diet_recommendation(client, target_date, context=context)
    except Exception as e:
        logger.warning('Failed to generate diet recommendation: %s', e, exc_info=True)

    return training_rec, diet_rec
