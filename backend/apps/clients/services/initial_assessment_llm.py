"""
Initial assessment helpers for recommendation / LLM consumers.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from django.conf import settings
from openai import OpenAI

logger = logging.getLogger(__name__)

OUTPUT_SCHEMA = {
    "risk_level": "LOW | MODERATE | HIGH | CRITICAL",
    "analysis": "Short explanation of user condition",
    "training_plan": {
        "type": "LOW_INTENSITY | MODERATE | HIGH_INTENSITY | RECOVERY",
        "duration_minutes": 30,
        "activities": [
            {
                "name": "",
                "description": "",
                "intensity": "low | moderate | high",
            }
        ],
    },
    "nutrition_plan": {
        "focus": "",
        "recommendations": [""],
        "restrictions": [""],
    },
    "warnings": [""],
    "coach_message": "Motivational but realistic message",
}


def _safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def detect_risk(medical_data: dict[str, Any] | None) -> str:
    """Detect baseline metabolic risk from medical markers."""
    medical_data = medical_data or {}
    triglycerides = _safe_float(medical_data.get("triglycerides"))
    glucose = _safe_float(medical_data.get("glucose"))
    cholesterol = _safe_float(medical_data.get("cholesterol"))

    if triglycerides is not None and triglycerides > 1000:
        return "CRITICAL"
    if triglycerides is not None and triglycerides > 500:
        return "HIGH"
    if (glucose is not None and glucose > 125) or (cholesterol is not None and cholesterol > 240):
        return "MODERATE"
    return "LOW"


def _daily_recovery_override(daily_checkin: dict[str, Any] | None) -> bool:
    daily_checkin = daily_checkin or {}
    sleep_quality = _safe_float(daily_checkin.get("sleep_quality"))
    energy_level = _safe_float(daily_checkin.get("energy_level"))
    fatigue = _safe_float(daily_checkin.get("fatigue"))
    return (
        (sleep_quality is not None and sleep_quality < 5)
        or (energy_level is not None and energy_level < 5)
        or (fatigue is not None and fatigue > 7)
    )


def _risk_rank(level: str) -> int:
    return {"LOW": 1, "MODERATE": 2, "HIGH": 3, "CRITICAL": 4}.get((level or "").upper(), 1)


def _max_risk(a: str, b: str) -> str:
    return a if _risk_rank(a) >= _risk_rank(b) else b


def _build_fallback_plan(payload: dict[str, Any], risk_level: str, force_recovery: bool) -> dict[str, Any]:
    profile = payload.get("user_profile") or {}
    goal = payload.get("goal") or "improve health"

    warnings: list[str] = []
    activities = [
        {
            "name": "Walking",
            "description": "Steady pace walking to improve circulation and fat metabolism with low joint stress.",
            "intensity": "low",
        },
        {
            "name": "Mobility routine",
            "description": "Gentle mobility and breathing work to support recovery and consistency.",
            "intensity": "low",
        },
    ]
    plan_type = "LOW_INTENSITY"
    duration = 30
    if force_recovery:
        plan_type = "RECOVERY"
        duration = 20
        warnings.append("Low readiness indicators detected today; keep activity light and restorative.")
    elif risk_level == "LOW":
        plan_type = "MODERATE"
        duration = 35
        activities = [
            {
                "name": "Brisk walking",
                "description": "Moderate pace cardio to improve conditioning without excessive fatigue.",
                "intensity": "moderate",
            },
            {
                "name": "Bodyweight strength circuit",
                "description": "Short full-body routine with controlled tempo and adequate rest.",
                "intensity": "moderate",
            },
        ]

    if risk_level in {"HIGH", "CRITICAL"}:
        warnings.append("Avoid HIIT, max intervals, and very high intensity efforts until biomarkers stabilize.")
    if risk_level == "CRITICAL":
        warnings.append("Very high triglycerides can raise pancreatitis and cardiovascular risk; urgent medical follow-up is recommended.")
    elif risk_level == "HIGH":
        warnings.append("Elevated triglycerides indicate significant metabolic stress; medical supervision is recommended.")
    elif risk_level == "MODERATE":
        warnings.append("Metabolic markers are above ideal range; prioritize consistency and conservative progression.")

    focus = "Improve metabolic health and support safe fat loss"
    recommendations = [
        "Build meals around vegetables, lean protein, and high-fiber carbs.",
        "Hydrate consistently throughout the day.",
        "Prioritize regular meal timing and portion control.",
    ]
    restrictions = ["Avoid sugary drinks and desserts.", "Limit refined flours and ultra-processed foods."]
    if risk_level in {"HIGH", "CRITICAL"}:
        focus = "Reduce triglycerides and stabilize glucose safely"
        restrictions.append("Avoid alcohol completely until labs improve.")

    name = profile.get("name") or "there"
    return {
        "risk_level": risk_level,
        "analysis": f"Plan adapted for {risk_level.lower()} metabolic risk with a conservative training approach toward '{goal}'.",
        "training_plan": {
            "type": plan_type,
            "duration_minutes": duration,
            "activities": activities,
        },
        "nutrition_plan": {
            "focus": focus,
            "recommendations": recommendations,
            "restrictions": restrictions,
        },
        "warnings": warnings or ["Monitor symptoms and recovery daily."],
        "coach_message": f"{name}, we will prioritize safe consistency first. Small daily wins will build momentum and better health.",
    }


def _build_system_prompt(pre_risk: str, force_recovery: bool) -> str:
    return f"""You are an AI Fitness & Nutrition Coach with clinical awareness.

Your job:
1) detect metabolic risk
2) avoid harmful recommendations
3) adapt training and nutrition conservatively when risk is present
4) return strict JSON only

Hard rules:
- If glucose > 125, triglycerides > 500, triglycerides > 1000, or cholesterol > 240, user has metabolic risk.
- triglycerides > 1000 = CRITICAL risk.
- For HIGH or CRITICAL risk: never prescribe HIIT, max intervals, insanity max, or high intensity.
- If sleep_quality < 5 OR energy_level < 5 OR fatigue > 7, reduce intensity and favor RECOVERY/light activity.
- Be protective, specific, and realistic.
- You are not a doctor; include medical supervision warning when risk is HIGH/CRITICAL.

Risk pre-check from backend: {pre_risk}
Force recovery from daily check-in: {str(force_recovery).lower()}

Return JSON with exactly this shape:
{json.dumps(OUTPUT_SCHEMA, ensure_ascii=False, indent=2)}
"""


def _get_openai_client() -> OpenAI | None:
    key = getattr(settings, "OPENAI_API_KEY", "") or ""
    if not key.strip():
        return None
    return OpenAI(api_key=key)


def _normalize_output(ai_data: dict[str, Any], fallback: dict[str, Any], risk_level: str, force_recovery: bool) -> dict[str, Any]:
    out = dict(fallback)
    out.update(
        {
            "risk_level": str(ai_data.get("risk_level") or fallback["risk_level"]).upper(),
            "analysis": str(ai_data.get("analysis") or fallback["analysis"]),
            "coach_message": str(ai_data.get("coach_message") or fallback["coach_message"]),
        }
    )
    out["risk_level"] = _max_risk(out["risk_level"], risk_level)
    if out["risk_level"] not in {"LOW", "MODERATE", "HIGH", "CRITICAL"}:
        out["risk_level"] = risk_level

    ai_tp = ai_data.get("training_plan") if isinstance(ai_data.get("training_plan"), dict) else {}
    current_tp = fallback["training_plan"]
    plan_type = str(ai_tp.get("type") or current_tp["type"]).upper()
    duration = ai_tp.get("duration_minutes")
    activities = ai_tp.get("activities") if isinstance(ai_tp.get("activities"), list) else current_tp["activities"]

    normalized_activities = []
    for item in activities[:8]:
        if not isinstance(item, dict):
            continue
        intensity = str(item.get("intensity") or "low").lower()
        if intensity not in {"low", "moderate", "high"}:
            intensity = "low"
        normalized_activities.append(
            {
                "name": str(item.get("name") or "Activity"),
                "description": str(item.get("description") or ""),
                "intensity": intensity,
            }
        )
    if not normalized_activities:
        normalized_activities = current_tp["activities"]

    disallow_high = out["risk_level"] in {"HIGH", "CRITICAL"} or force_recovery
    if disallow_high:
        if plan_type == "HIGH_INTENSITY":
            plan_type = "LOW_INTENSITY"
        if plan_type not in {"LOW_INTENSITY", "MODERATE", "RECOVERY"}:
            plan_type = "LOW_INTENSITY"
        if force_recovery:
            plan_type = "RECOVERY"
        for act in normalized_activities:
            if act["intensity"] == "high":
                act["intensity"] = "low"
            lowered_name = act["name"].lower()
            if "hiit" in lowered_name or "insanity" in lowered_name or "max interval" in lowered_name:
                act["name"] = "Walking"
                act["description"] = "Low-impact steady movement for safety and recovery."
                act["intensity"] = "low"

    if force_recovery and plan_type != "RECOVERY":
        plan_type = "RECOVERY"

    out["training_plan"] = {
        "type": plan_type if plan_type in {"LOW_INTENSITY", "MODERATE", "HIGH_INTENSITY", "RECOVERY"} else current_tp["type"],
        "duration_minutes": int(duration) if isinstance(duration, (int, float)) else current_tp["duration_minutes"],
        "activities": normalized_activities,
    }

    ai_np = ai_data.get("nutrition_plan") if isinstance(ai_data.get("nutrition_plan"), dict) else {}
    recommendations = ai_np.get("recommendations")
    restrictions = ai_np.get("restrictions")
    out["nutrition_plan"] = {
        "focus": str(ai_np.get("focus") or fallback["nutrition_plan"]["focus"]),
        "recommendations": [str(x) for x in recommendations]
        if isinstance(recommendations, list) and recommendations
        else fallback["nutrition_plan"]["recommendations"],
        "restrictions": [str(x) for x in restrictions]
        if isinstance(restrictions, list) and restrictions
        else fallback["nutrition_plan"]["restrictions"],
    }

    warnings = ai_data.get("warnings")
    out["warnings"] = [str(w) for w in warnings] if isinstance(warnings, list) and warnings else fallback["warnings"]
    return out


def generate_initial_assessment_coaching_plan(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Generate clinically-aware coaching JSON from dynamic assessment payload.
    Applies deterministic risk and readiness constraints even when LLM is used.
    """
    medical_data = payload.get("medical_data") if isinstance(payload, dict) else {}
    daily_checkin = payload.get("daily_checkin") if isinstance(payload, dict) else {}
    risk_level = detect_risk(medical_data)
    force_recovery = _daily_recovery_override(daily_checkin)
    fallback = _build_fallback_plan(payload if isinstance(payload, dict) else {}, risk_level, force_recovery)

    if risk_level == "CRITICAL":
        return fallback

    client = _get_openai_client()
    if not client:
        return fallback

    model = getattr(settings, "OPENAI_MODEL", "gpt-4o-mini")
    temperature = getattr(settings, "OPENAI_TEMPERATURE", 0.2)

    try:
        response = client.chat.completions.create(
            model=model,
            temperature=temperature,
            messages=[
                {"role": "system", "content": _build_system_prompt(risk_level, force_recovery)},
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False, indent=2)},
            ],
        )
        raw = (response.choices[0].message.content or "").strip()
        if raw.startswith("```"):
            raw = raw.split("```", 1)[1]
            if raw.lstrip().startswith("json"):
                raw = raw.lstrip()[4:]
            raw = raw.strip()
        data = json.loads(raw)
        if not isinstance(data, dict):
            return fallback
        return _normalize_output(data, fallback, risk_level, force_recovery)
    except Exception as exc:
        logger.warning("Initial assessment coaching generation failed: %s", exc, exc_info=True)
        return fallback


def build_initial_assessment_llm_payload(assessment) -> dict:
    """Return a single JSON-serializable dict suitable for LLM or internal pipelines."""
    return {
        'schema_version': '1.0',
        'assessment_id': assessment.pk,
        'client_id': assessment.client_id,
        'version': assessment.version,
        'is_active': assessment.is_active,
        'timestamps': {
            'created_at': assessment.created_at.isoformat() if assessment.created_at else None,
            'updated_at': assessment.updated_at.isoformat() if assessment.updated_at else None,
        },
        'created_by_user_id': assessment.created_by_id,
        'personal_data': {
            'nombre_completo': assessment.nombre_completo,
            'edad': assessment.edad,
            'fecha_nacimiento': str(assessment.fecha_nacimiento) if assessment.fecha_nacimiento else None,
            'telefono': assessment.telefono,
            'contacto_emergencia': assessment.contacto_emergencia,
            'peso_actual': str(assessment.peso_actual) if assessment.peso_actual is not None else None,
            'estatura': str(assessment.estatura) if assessment.estatura is not None else None,
            'correo_electronico': assessment.correo_electronico,
        },
        'health_history': {
            'estado_salud': assessment.estado_salud,
            'ultima_revision_medica': str(assessment.ultima_revision_medica)
            if assessment.ultima_revision_medica
            else None,
            'tiene_lesion_o_impedimento': assessment.tiene_lesion_o_impedimento,
            'lesion_o_impedimento_detalle': assessment.lesion_o_impedimento_detalle,
            'tiene_condicion_medica': assessment.tiene_condicion_medica,
            'condicion_medica_detalle': assessment.condicion_medica_detalle,
            'alergias': assessment.alergias,
            'medicamentos_actuales': assessment.medicamentos_actuales,
            'suplementos_actuales': assessment.suplementos_actuales,
        },
        'lifestyle': {
            'fuma': assessment.fuma,
            'frecuencia_fuma': assessment.frecuencia_fuma,
            'consume_alcohol': assessment.consume_alcohol,
            'frecuencia_alcohol': assessment.frecuencia_alcohol,
            'ocupacion': assessment.ocupacion,
            'horas_sueno_promedio': str(assessment.horas_sueno_promedio)
            if assessment.horas_sueno_promedio is not None
            else None,
        },
        'physical_activity': {
            'actualmente_realiza_ejercicio': assessment.actualmente_realiza_ejercicio,
            'tipo_ejercicio_actual': assessment.tipo_ejercicio_actual,
            'dias_entrena_por_semana': assessment.dias_entrena_por_semana,
            'minutos_cardio_por_sesion': assessment.minutos_cardio_por_sesion,
            'minutos_fuerza_por_sesion': assessment.minutos_fuerza_por_sesion,
            'actividades_fisicas_favoritas': assessment.actividades_fisicas_favoritas,
        },
        'nutrition': {
            'sigue_dieta_actualmente': assessment.sigue_dieta_actualmente,
            'dieta_actual_detalle': assessment.dieta_actual_detalle,
            'ha_seguido_plan_alimentacion': assessment.ha_seguido_plan_alimentacion,
            'plan_alimentacion_detalle': assessment.plan_alimentacion_detalle,
            'quien_compra_y_prepara_comida': assessment.quien_compra_y_prepara_comida,
            'comidas_por_dia': assessment.comidas_por_dia,
        },
        'weight_history': {
            'peso_mas_bajo_ultimos_5_anios': str(assessment.peso_mas_bajo_ultimos_5_anios)
            if assessment.peso_mas_bajo_ultimos_5_anios is not None
            else None,
            'peso_mas_alto_ultimos_5_anios': str(assessment.peso_mas_alto_ultimos_5_anios)
            if assessment.peso_mas_alto_ultimos_5_anios is not None
            else None,
            'objetivo_peso': assessment.objetivo_peso,
        },
        'goals_and_motivation': {
            'metas_salud_fitness': assessment.metas_salud_fitness,
            'obstaculos_principales': assessment.obstaculos_principales,
            'fortalezas_personales': assessment.fortalezas_personales,
            'importancia_meta_1_10': assessment.importancia_meta_1_10,
            'confianza_meta_1_10': assessment.confianza_meta_1_10,
        },
        'consent': {
            'declaracion_aceptada': assessment.declaracion_aceptada,
            'nombre_cliente_consentimiento': assessment.nombre_cliente_consentimiento,
            'firma_texto': assessment.firma_texto,
            'fecha_consentimiento': str(assessment.fecha_consentimiento)
            if assessment.fecha_consentimiento
            else None,
        },
        'attachment': {
            'has_file': bool(assessment.documento_adjunto),
            'relative_path': assessment.documento_adjunto.name if assessment.documento_adjunto else None,
            'original_filename': assessment.documento_nombre_original or None,
            'size_bytes': assessment.documento_tamano_bytes,
            'content_type': assessment.documento_content_type or None,
        },
    }
