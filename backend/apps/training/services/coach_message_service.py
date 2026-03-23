"""Deterministic coach message builder from recommendation context."""

from __future__ import annotations


class CoachMessageService:
    """Generates supportive, risk-aware Spanish coach messages."""

    def build_message(
        self,
        recommendation_type: str,
        readiness_band: str,
        warnings: list[str],
        checkin_flags: dict[str, bool],
    ) -> str:
        if checkin_flags.get("injury") or "pain_or_injury" in warnings:
            return (
                "La combinacion de dolor reportado y fatiga elevada sugiere descanso o movilidad suave, "
                "no carga intensa."
            )

        if checkin_flags.get("high_motivation_poor_recovery"):
            return (
                "Tu motivacion esta alta, pero la recuperacion no acompana. "
                "Hoy gana mas una sesion prudente para proteger rendimiento manana."
            )

        if "stress_high" in warnings:
            return (
                "Hoy tienes energia para entrenar, pero el estres viene elevado. "
                "Conviene una sesion moderada en lugar de maxima intensidad."
            )

        if readiness_band in {"high", "good"} and recommendation_type in {"insanity_max", "insanity_moderate"}:
            return "Buen nivel de preparacion hoy. Entrena con tecnica, controla ritmo y reserva margen para recuperarte bien."

        if recommendation_type in {"mobility_recovery", "cardio_light", "full_rest"}:
            return "Hoy priorizamos recuperacion inteligente para sostener progreso y volver mas fuerte manana."

        return "Sesion ajustada a tu estado de hoy: calidad de movimiento primero, intensidad con control."
