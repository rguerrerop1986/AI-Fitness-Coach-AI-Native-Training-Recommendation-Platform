# AI Recommendation System Architecture

This document describes the architecture of the AI-powered recommendation system used by the **AI Fitness Coach** platform. The system generates personalized daily diet and training plans using LLM reasoning, contextual user data, and retrieval-based knowledge.

A high-level diagram is available at [ai-architecture.png](ai-architecture.png).

---

## Pipeline Overview

The recommendation pipeline flows as follows:

1. **User Check-in** → Client submits daily readiness (sleep, energy, motivation, etc.).
2. **Context Builder** → Aggregates profile, history, and catalog data.
3. **User State Engine** → Derives readiness indicators and constraints.
4. **Memory Layer** → Provides historical recommendations and adherence data.
5. **Coach Agent** → Orchestrates strategy and candidate selection.
6. **Prompt Engine** → Builds the structured prompt for the LLM.
7. **LLM Reasoning Layer** → Produces the daily plan (diet + training) as structured JSON.
8. **Evaluation Layer** → Validates IDs and constraints before persistence.
9. **Persisted Training Plan** → Stored in the database and exposed to the client.

---

## Context Builder

The **Context Builder** assembles all inputs required for the AI:

- **User profile**: Demographics, body metrics (height, weight), goals, and constraints.
- **Daily check-in**: Sleep quality, energy level, motivation, stress, muscle soreness, readiness to train, hydration, diet adherence, preferred training mode, and free-text comments.
- **Recent history**: Last training group and intensity, previous recommendations, recent check-ins and training logs.
- **Allowed catalogs**: Lists of allowed foods and exercises (including videos) with IDs and metadata. The LLM may only select from these IDs.

This context is passed as a structured JSON payload to the Prompt Engine so the LLM receives consistent, reliable input.

---

## User State Engine

The **User State Engine** turns raw check-in and history data into structured readiness signals:

- **Recovery indicators**: Derived from sleep quality, soreness, and previous session intensity.
- **Fatigue / energy**: From energy level, stress, and recent RPE or logs.
- **Adherence**: From diet adherence and workout adherence over recent days.
- **Readiness classification**: Informs whether to recommend intense training, moderate workout, or recovery.

These signals are embedded in the context payload and guide the Coach Agent and LLM toward safe, appropriate recommendations (e.g., recovery when the user is fatigued).

---

## Memory Layer

The **Memory Layer** provides historical awareness:

- **Previous workouts**: Training logs, RPE, pain level, and execution status.
- **Historical recommendations**: Recent daily training and diet recommendations (type, group, intensity).
- **Adherence and trends**: Check-in history and adherence over time.

This allows the system to avoid repeating the same stimulus, respect recovery, and align with long-term patterns (e.g., alternating upper/lower body, avoiding back-to-back high-intensity days).

---

## Coach Agent

The **Coach Agent** is the decision-making orchestrator (implemented across the backend services):

- **Analyzes user readiness** using the User State and Memory Layer.
- **Selects strategy**: e.g., recovery vs. strength vs. hybrid vs. video-based.
- **Retrieves relevant candidates**: Builds the allowed lists of foods and exercises (including videos) from the catalog.
- **Determines constraints**: Allowed training groups, modalities, and intensity bounds.
- **Prepares context for the LLM**: Passes the full context package to the Prompt Engine.

The agent ensures the LLM receives only valid options and clear constraints so outputs are actionable and safe.

---

## Prompt Engine

The **Prompt Engine** builds the LLM prompt:

- **System prompt**: Defines the coach persona, strict rules (e.g., only use provided food_id and exercise_id), allowed enums (training_group, modality), and the exact JSON output schema.
- **User content**: The structured context (client, today_checkin, recent_history, allowed_foods, allowed_exercises) serialized as JSON.

Prompt construction lives in modules such as `apps.client_portal.services.ai_daily_plan` (daily diet + training plan) and `apps.training.services.openai_coach` (single-exercise or candidate selection). The engine ensures **contextual prompts** that include user state and retrieval-based knowledge.

---

## LLM Reasoning Layer

The **LLM Reasoning Layer** calls the language model (e.g., OpenAI API) with the prepared messages:

- **Input**: System prompt + user context (structured JSON).
- **Output**: A single JSON object containing:
  - **Diet plan**: Title, goal, total calories, coach message, and meals (each meal with meal_type and list of { food_id, quantity, unit }).
  - **Training plan**: recommendation_type, training_group, modality, intensity_level, coach_message, reasoning_summary, recommended_video_exercise_id (or null), and exercises (list of { exercise_id, sets, reps, rest_seconds }).

The model is instructed to use only IDs from the allowed catalogs and to align recommendations with recovery, energy, and user preferences. Response parsing strips markdown code fences and parses JSON; failed or invalid responses trigger fallback or retry logic.

---

## Evaluation Layer

Before persisting, the **Evaluation Layer** validates the LLM output:

- **Catalog validation**: Every food_id must exist in the Food catalog; every exercise_id in the Exercise catalog; recommended_video_exercise_id must be null or exist in the TrainingVideo catalog.
- **Enum validation**: training_group and modality must be from the allowed choices.
- **Safety and consistency**: Invalid or missing IDs are filtered out; if the result is empty or incoherent, the system may fall back to a non-LLM recommendation or return an error.

Only after validation are `DailyDietRecommendation`, `DailyDietRecommendationMeal`, `DailyDietRecommendationMealFood`, `DailyTrainingRecommendation`, and `DailyTrainingRecommendationExercise` (and optional video) persisted. This keeps the database consistent and prevents invalid or unsafe plans from being shown to the user.

---

## Summary

Together, these components form an **AI-native recommendation system** that:

- Uses **LLM reasoning** for personalized daily plans.
- Relies on **contextual prompts** built from user state and **retrieval-based training knowledge** (catalogs).
- Maintains a **memory layer** for historical awareness.
- Enforces an **evaluation layer** for safety and data integrity.
- Exposes a **recommendation engine** (Coach Agent + Prompt Engine + LLM + Evaluation) suitable for production use.

For implementation details, see the backend modules under `apps.client_portal.services`, `apps.training.services`, and `apps.recommendations`.
