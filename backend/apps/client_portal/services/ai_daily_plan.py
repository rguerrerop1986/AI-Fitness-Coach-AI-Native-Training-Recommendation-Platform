"""
AI-powered daily plan: build context from readiness + history + catalog, call OpenAI,
validate response (only catalog IDs), persist DailyDietRecommendation + DailyTrainingRecommendation.
"""
import json
import logging
from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.clients.models import Client
from apps.catalogs.models import Food, Exercise
from apps.training.models import TrainingVideo
from apps.tracking.models import (
    DailyReadinessCheckin,
    DailyTrainingRecommendation,
    DailyTrainingRecommendationExercise,
    DailyDietRecommendation,
    DailyDietRecommendationMeal,
    DailyDietRecommendationMealFood,
)
from apps.client_portal.services.daily_recommendation_service import (
    build_client_recommendation_context,
)
from apps.training.services.openai_coach import get_openai_client

logger = logging.getLogger(__name__)

ALLOWED_TRAINING_GROUPS = {c[0] for c in DailyTrainingRecommendation.TrainingGroup.choices}
ALLOWED_MODALITIES = {c[0] for c in DailyTrainingRecommendation.Modality.choices}


def _build_ai_context(
    client: Client,
    readiness: DailyReadinessCheckin,
    target_date: date,
) -> Dict[str, Any]:
    """Build user payload matching the coach prompt template: client, today_checkin, recent_history, allowed_foods, allowed_exercises."""
    ctx = build_client_recommendation_context(client, target_date)

    latest = client.measurements.first()
    weight_kg = None
    if latest and latest.weight_kg is not None:
        weight_kg = float(latest.weight_kg)
    elif client.initial_weight_kg is not None:
        weight_kg = float(client.initial_weight_kg)

    height_cm = None
    if client.height_m is not None:
        try:
            height_cm = int(round(float(client.height_m) * 100))
        except (TypeError, ValueError):
            pass

    gender = (getattr(client, "sex", None) or "").lower()
    if gender == "M":
        gender = "male"
    elif gender == "F":
        gender = "female"
    elif gender == "O":
        gender = "other"

    client_payload = {
        "id": client.id,
        "name": client.full_name,
        "gender": gender or None,
        "height_cm": height_cm,
        "weight_kg": weight_kg,
    }

    today_checkin = {
        "sleep_quality": readiness.sleep_quality,
        "diet_adherence_yesterday": readiness.diet_adherence_yesterday,
        "motivation_today": readiness.motivation_today,
        "energy_level": readiness.energy_level,
        "stress_level": readiness.stress_level,
        "muscle_soreness": readiness.muscle_soreness,
        "readiness_to_train": readiness.readiness_to_train,
        "mood": readiness.mood,
        "hydration_level": readiness.hydration_level,
        "yesterday_training_intensity": readiness.yesterday_training_intensity,
        "slept_poorly": readiness.slept_poorly,
        "ate_poorly_yesterday": readiness.ate_poorly_yesterday,
        "feels_100_percent": readiness.feels_100_percent,
        "wants_video_today": readiness.wants_video_today,
        "preferred_training_mode": readiness.preferred_training_mode or "auto",
        "comments": readiness.comments or "",
    }

    yesterday_training = ctx.get("yesterday_training")
    last_training_group = None
    last_training_intensity = None
    if yesterday_training:
        last_training_group = getattr(yesterday_training, "training_group", None) or ""
        last_training_intensity = getattr(
            readiness, "yesterday_training_intensity", None
        )

    last_recommendations = [
        {
            "date": r.date.isoformat(),
            "recommendation_type": r.recommendation_type,
            "training_group": getattr(r, "training_group", "") or "",
        }
        for r in (ctx.get("recent_training_recommendations") or [])[:5]
    ]
    recent_checkins = [
        {
            "date": c.date.isoformat(),
            "fatigue": c.fatigue,
            "diet_adherence": c.diet_adherence,
            "rpe": c.rpe,
        }
        for c in (ctx.get("recent_checkins") or [])[:7]
    ]

    recent_history = {
        "last_training_group": last_training_group,
        "last_training_intensity": last_training_intensity,
        "last_recommendations": last_recommendations,
        "recent_checkins": recent_checkins,
    }

    allowed_foods: List[Dict[str, Any]] = [
        {"id": f.id, "name": f.name}
        for f in Food.objects.filter(is_active=True)[:80]
    ]

    # Combined list: exercises (type "exercise") + videos (type "video"). Model uses id from type=video for recommended_video_exercise_id.
    allowed_exercises: List[Dict[str, Any]] = []
    for e in Exercise.objects.filter(is_active=True)[:80]:
        allowed_exercises.append({
            "id": e.id,
            "name": e.name,
            "type": "exercise",
            "muscle_group": e.muscle_group or "",
        })
    for v in TrainingVideo.objects.filter(is_active=True)[:40]:
        allowed_exercises.append({
            "id": v.id,
            "name": v.name,
            "type": "video",
            "muscle_group": getattr(v, "category", "") or "cardio",
        })

    return {
        "client": client_payload,
        "today_checkin": today_checkin,
        "recent_history": recent_history,
        "allowed_foods": allowed_foods,
        "allowed_exercises": allowed_exercises,
    }


_SYSTEM_PROMPT = """Eres un coach experto en entrenamiento y nutrición personalizada.
Tu tarea es generar un plan diario de dieta y entrenamiento estrictamente a partir del contexto del usuario y de catálogos permitidos.

Reglas obligatorias:
1. Solo puedes seleccionar alimentos usando food_id de la lista permitida (allowed_foods).
2. Solo puedes seleccionar ejercicios usando exercise_id de la lista permitida (allowed_exercises con type "exercise"); para video usa el id de un ítem con type "video" en recommended_video_exercise_id.
3. No inventes alimentos ni ejercicios.
4. Ajusta la intensidad del entrenamiento según recuperación, sueño, energía, motivación, adherencia dietaria y carga previa.
5. Si el usuario no está en buen estado, prioriza recuperación activa, movilidad o menor intensidad.
6. Si el usuario está en muy buen estado, puedes recomendar fuerza, híbrido o video tipo Insanity según preferencias y contexto.
7. Devuelve únicamente JSON válido, sin texto antes ni después.
8. El campo training_group debe ser uno de: upper_body, lower_body, core, full_body, insanity, active_recovery
9. El campo modality debe ser uno de: insanity, hybrid, gym_strength, mobility_recovery, auto
10. El plan debe ser realista, seguro y coherente con el estado actual del usuario.

Formato de respuesta (JSON exacto):

{
  "diet_plan": {
    "title": "Plan diario personalizado",
    "goal": "Mantenimiento",
    "total_calories": 1700,
    "coach_message": "Mensaje breve para el usuario.",
    "meals": [
      {
        "meal_type": "breakfast",
        "foods": [
          { "food_id": 1, "quantity": 2, "unit": "pieza" }
        ]
      }
    ]
  },
  "training_plan": {
    "recommendation_type": "recovery",
    "training_group": "active_recovery",
    "modality": "hybrid",
    "intensity_level": 3,
    "coach_message": "Mensaje breve para el usuario.",
    "reasoning_summary": "Resumen del razonamiento.",
    "recommended_video_exercise_id": null,
    "exercises": []
  }
}

- meal_type: breakfast | lunch | dinner | snack | pre_workout | post_workout
- recommendation_type: recovery | strength | mobility | cardio | core | hiit | full_body | rest_day
- recommended_video_exercise_id: id de un ítem con type "video" en allowed_exercises, o null
- exercises: lista de { "exercise_id": <id>, "sets": N, "reps": N, "rest_seconds": N } usando solo ids con type "exercise"
"""


def build_daily_recommendation_prompt(context: Dict[str, Any]) -> Tuple[str, str]:
    """Return (system_prompt, user_content) for OpenAI."""
    system = _SYSTEM_PROMPT
    user_content = json.dumps(context, indent=2, ensure_ascii=False)
    return system, user_content


def _call_openai_for_plan(context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    client = get_openai_client()
    if not client:
        return None

    system, user_content = build_daily_recommendation_prompt(context)
    model = getattr(settings, "OPENAI_MODEL", "gpt-4o-mini")
    temperature = getattr(settings, "OPENAI_TEMPERATURE", 0.2)

    for attempt in range(2):
        try:
            resp = client.chat.completions.create(
                model=model,
                temperature=temperature if attempt == 0 else 0.0,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_content},
                ],
            )
            raw = resp.choices[0].message.content.strip()
            if raw.startswith("```"):
                raw = raw.split("```", 1)[1]
                if raw.startswith("json"):
                    raw = raw[4:]
                raw = raw.strip()
            data = json.loads(raw)
            return data
        except Exception as e:
            logger.warning("AI daily plan attempt %s failed: %s", attempt + 1, e, exc_info=True)
    return None


def _validate_and_persist_plan(
    client: Client,
    target_date: date,
    ai_data: Dict[str, Any],
) -> Tuple[Optional[DailyTrainingRecommendation], Optional[DailyDietRecommendation]]:
    """Validate IDs and choices, persist daily recommendation. Return (training_rec, diet_rec)."""
    diet = ai_data.get("diet_plan") or {}
    training = ai_data.get("training_plan") or {}

    meal_specs = diet.get("meals") or []
    food_ids = set()
    for m in meal_specs:
        for f in m.get("foods") or []:
            fid = f.get("food_id")
            if fid is not None:
                food_ids.add(fid)
    foods_qs = {f.id: f for f in Food.objects.filter(id__in=food_ids, is_active=True)}

    validated_meals = []
    for m in meal_specs:
        valid_foods = [
            f for f in (m.get("foods") or [])
            if f.get("food_id") in foods_qs
        ]
        if valid_foods:
            validated_meals.append({"meal_type": m.get("meal_type") or "snack", "title": m.get("title") or "", "foods": valid_foods})

    ex_specs = training.get("exercises") or []
    ex_ids = {e.get("exercise_id") for e in ex_specs if e.get("exercise_id") is not None}
    ex_qs = {e.id: e for e in Exercise.objects.filter(id__in=ex_ids, is_active=True)}
    ex_specs = [e for e in ex_specs if e.get("exercise_id") in ex_qs]

    video_id = training.get("recommended_video_exercise_id")
    video_obj = None
    if video_id is not None:
        video_obj = TrainingVideo.objects.filter(id=video_id, is_active=True).first()
        if not video_obj:
            video_id = None

    training_group = (training.get("training_group") or "").strip()
    if training_group not in ALLOWED_TRAINING_GROUPS:
        training_group = DailyTrainingRecommendation.TrainingGroup.FULL_BODY
    modality = (training.get("modality") or "").strip()
    if modality not in ALLOWED_MODALITIES:
        modality = DailyTrainingRecommendation.Modality.AUTO

    has_any_foods = bool(validated_meals)
    has_any_exercises = bool(ex_specs)
    has_video = video_obj is not None
    if not has_any_foods and not has_any_exercises and not has_video:
        logger.warning(
            "AI daily plan returned no valid foods/exercises/videos after validation for client %s",
            client.id,
        )
        return None, None

    rec_type = (training.get("recommendation_type") or "").strip()
    if rec_type not in {c[0] for c in DailyTrainingRecommendation.RecommendationType.choices}:
        rec_type = DailyTrainingRecommendation.RecommendationType.STRENGTH

    diet_rec = None
    training_rec = None

    with transaction.atomic():
        if has_any_foods:
            diet_rec = DailyDietRecommendation.objects.create(
                client=client,
                date=target_date,
                title=diet.get("title") or "Plan diario personalizado",
                goal=diet.get("goal") or "Mantenimiento",
                coach_message=diet.get("coach_message") or "",
                reasoning_summary="Generado por motor IA contextual.",
                total_calories=diet.get("total_calories"),
            )
            for order, meal in enumerate(validated_meals, 1):
                meal_obj = DailyDietRecommendationMeal.objects.create(
                    recommendation=diet_rec,
                    meal_type=meal.get("meal_type") or "snack",
                    title=meal.get("title") or "",
                    description="",
                    order=order,
                )
                for idx, f_spec in enumerate(meal.get("foods") or [], 1):
                    food_obj = foods_qs.get(f_spec.get("food_id"))
                    if not food_obj:
                        continue
                    qty = f_spec.get("quantity")
                    if qty is None:
                        qty = Decimal("1")
                    else:
                        qty = Decimal(str(qty))
                    DailyDietRecommendationMealFood.objects.create(
                        meal=meal_obj,
                        food=food_obj,
                        quantity=qty,
                        unit=f_spec.get("unit") or "g",
                        order=idx,
                    )

        if has_any_exercises or has_video:
            training_rec = DailyTrainingRecommendation.objects.create(
                client=client,
                date=target_date,
                recommendation_type=rec_type,
                training_group=training_group,
                modality=modality,
                intensity_level=training.get("intensity_level"),
                coach_message=training.get("coach_message") or "",
                reasoning_summary=training.get("reasoning_summary") or "",
                warnings="",
                recommended_video=video_obj,
            )
            for order, ex_spec in enumerate(ex_specs, 1):
                ex_obj = ex_qs.get(ex_spec.get("exercise_id"))
                if not ex_obj:
                    continue
                DailyTrainingRecommendationExercise.objects.create(
                    recommendation=training_rec,
                    exercise=ex_obj,
                    order=order,
                    sets=ex_spec.get("sets") or 0,
                    reps=ex_spec.get("reps") or 0,
                    rest_seconds=ex_spec.get("rest_seconds"),
                )

    return training_rec, diet_rec


def generate_ai_daily_plan(
    client: Client,
    readiness: DailyReadinessCheckin,
    target_date: Optional[date] = None,
) -> Tuple[Optional[DailyTrainingRecommendation], Optional[DailyDietRecommendation]]:
    """
    Build context, call OpenAI, validate JSON and IDs, persist and return
    (training_rec, diet_rec). Returns existing if already present for that date.
    """
    target_date = target_date or timezone.localdate()

    existing_training = DailyTrainingRecommendation.objects.filter(
        client=client, date=target_date
    ).first()
    existing_diet = DailyDietRecommendation.objects.filter(
        client=client, date=target_date
    ).first()
    if existing_training or existing_diet:
        return existing_training, existing_diet

    context = _build_ai_context(client, readiness, target_date)
    ai_data = _call_openai_for_plan(context)
    if not ai_data:
        logger.warning("AI daily plan unavailable; returning None for client %s", client.id)
        return None, None

    return _validate_and_persist_plan(client, target_date, ai_data)
