# Módulo Training – Recomendaciones diarias de entrenamiento

Módulo Django para el flujo de recomendación diaria inspirado en Insanity: check-in → evaluación de readiness → selección de candidatos → recomendación con OpenAI → registro del workout → análisis de feedback.

---

## 1. Resumen de arquitectura

- **Capas**
  - **Modelos**: `TrainingVideo`, `DailyCheckIn`, `WorkoutLog`, `TrainingRecommendation`.
  - **Selectors**: consultas de solo lectura (`get_recent_workout_logs`, `get_checkin_for_date`).
  - **Servicios**:
    - **ReadinessEvaluator** (`services/readiness.py`): reglas determinísticas (sueño, energía, dolor articular, soreness, RPE reciente) → `score`, `warnings`, `allowed_intensity`.
    - **VideoSelector** (`services/video_selector.py`): filtra 3–5 videos seguros según readiness y check-in.
    - **OpenAICoachService** (`services/openai_coach.py`): elige un workout entre los candidatos y devuelve `recommended_workout_id`, `recommendation_type`, `reasoning_summary`, `warnings`, `coach_message`.
    - **TrainingRecommendationService** (`services/recommendation_service.py`): orquesta check-in → historial → readiness → candidatos → OpenAI → persistencia.
    - **Feedback analysis** (`services/feedback_analysis.py`): análisis post-workout con OpenAI (summary, coach_comment, tomorrow_hint).

- **Flujo**
  1. Usuario crea `DailyCheckIn` (POST checkins).
  2. Usuario pide recomendación (POST recommendations/generate) → se evalúa readiness, se filtran candidatos, OpenAI elige uno, se guarda `TrainingRecommendation`.
  3. Usuario registra resultado (POST workout-logs).
  4. Usuario puede analizar feedback (POST workout-feedback/analyze).

---

## 2. Archivos creados / modificados

### Nuevos (app `training`)

| Archivo | Descripción |
|--------|-------------|
| `apps/training/__init__.py` | Init del módulo |
| `apps/training/apps.py` | AppConfig |
| `apps/training/models.py` | TrainingVideo, DailyCheckIn, WorkoutLog, TrainingRecommendation |
| `apps/training/admin.py` | Registro en admin |
| `apps/training/selectors.py` | get_recent_workout_logs, get_checkin_for_date |
| `apps/training/serializers.py` | Serializers para check-in, workout log, recomendación, feedback |
| `apps/training/views.py` | CheckIn, GenerateRecommendation, WorkoutLog, WorkoutFeedbackAnalyze |
| `apps/training/urls.py` | Rutas bajo `/api/training/` |
| `apps/training/services/readiness.py` | Evaluación determinística de readiness |
| `apps/training/services/video_selector.py` | Selección de videos candidatos |
| `apps/training/services/openai_coach.py` | Cliente OpenAI y recomendación desde candidatos |
| `apps/training/services/recommendation_service.py` | Orquestación del flujo de recomendación |
| `apps/training/services/feedback_analysis.py` | Análisis de feedback post-workout con OpenAI |
| `apps/training/management/commands/seed_insanity_videos.py` | Comando para cargar catálogo Insanity |
| `apps/training/migrations/0001_initial.py` | Migración inicial (existente) |
| `apps/training/migrations/0002_...` | Ajustes de modelos (constraints, campos) |
| `apps/training/tests/test_readiness.py` | Tests de readiness (dolor articular, energía alta) |
| `apps/training/tests/test_video_selector.py` | Tests del selector (exclusión explosivos con dolor piernas) |
| `apps/training/tests/test_api.py` | Tests del endpoint de recomendación con mock OpenAI |
| `apps/training/tests/conftest.py` | Configuración pytest para Django |

### Modificados

| Archivo | Cambio |
|--------|--------|
| `fitness_coach/settings.py` | `apps.training` en INSTALLED_APPS; OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TEMPERATURE |
| `fitness_coach/urls.py` | `path('api/training/', include('apps.training.urls'))` |
| `requirements.txt` | Añadido `openai>=1.0.0` |

---

## 3. Instrucciones para migraciones

Desde la raíz del backend:

```bash
cd backend
pip install -r requirements.txt   # incluye openai
python manage.py migrate training
```

Si ya existía la app y solo añadiste cambios, aplicar la última migración:

```bash
python manage.py migrate
```

---

## 4. Variables de entorno necesarias

Añade en `.env` (o `env.example`):

```env
# OpenAI (recomendaciones y análisis de feedback)
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
OPENAI_TEMPERATURE=0.3
```

- **OPENAI_API_KEY**: obligatoria para generar recomendaciones y analizar feedback; si falta, se usan fallbacks (primer candidato, mensajes genéricos).
- **OPENAI_MODEL**: modelo para JSON (por defecto `gpt-4o-mini`).
- **OPENAI_TEMPERATURE**: baja (p. ej. 0.3) para respuestas estables.

---

## 5. Ejemplos de requests (curl / httpie)

Base URL: `http://localhost:8000` (o la que uses). Todas las rutas requieren **JWT** en `Authorization: Bearer <access_token>`.

### Obtener token (login)

```bash
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"tu_usuario","password":"tu_password"}'
```

Usa el `access` del JSON en los ejemplos siguientes como `TOKEN`.

### 1. Crear check-in

```bash
curl -X POST http://localhost:8000/api/training/checkins/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "date": "2026-03-07",
    "hours_sleep": 7,
    "sleep_quality": 8,
    "energy_level": 7,
    "motivation_level": 8,
    "soreness_legs": 3,
    "joint_pain": false,
    "wants_intensity": true,
    "notes": ""
  }'
```

### 2. Generar recomendación

```bash
curl -X POST http://localhost:8000/api/training/recommendations/generate/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"date": "2026-03-07"}'
```

Ejemplo de respuesta:

```json
{
  "date": "2026-03-07",
  "recommended_video": {
    "id": 2,
    "name": "Cardio Power and Resistance",
    "category": "mixed",
    "difficulty": "medium",
    "duration_minutes": 40
  },
  "recommendation_type": "moderate",
  "reasoning_summary": "Good energy and no pain signals. Moderate intensity fits better than max effort today.",
  "warnings": "Reduce impact if legs feel heavier than expected.",
  "coach_message": "Train with intensity, but stay controlled."
}
```

### 3. Registrar resultado de entrenamiento

```bash
curl -X POST http://localhost:8000/api/training/workout-logs/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "date": "2026-03-07",
    "video": 2,
    "completed": true,
    "rpe": 7,
    "satisfaction": 8,
    "felt_strong": true,
    "pain_during_workout": false,
    "body_feedback": "Legs heavy at the end.",
    "emotional_feedback": "Good session."
  }'
```

### 4. Analizar feedback post-workout

Por `workout_log_id`:

```bash
curl -X POST http://localhost:8000/api/training/workout-feedback/analyze/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"workout_log_id": 1}'
```

O con payload directo:

```bash
curl -X POST http://localhost:8000/api/training/workout-feedback/analyze/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "video_name": "Cardio Power and Resistance",
    "completed": true,
    "rpe": 7,
    "satisfaction": 8,
    "felt_strong": true,
    "pain_during_workout": false,
    "body_feedback": "Legs heavy at the end.",
    "emotional_feedback": "Good session."
  }'
```

Respuesta esperada:

```json
{
  "summary": "Solid session with high satisfaction and no pain.",
  "coach_comment": "Keep that consistency; consider a recovery day if legs stay heavy.",
  "tomorrow_hint": "If legs recover well, you can go moderate again; otherwise choose recovery."
}
```

### Con httpie

```bash
# Check-in
http POST http://localhost:8000/api/training/checkins/ "Authorization: Bearer TOKEN" date=2026-03-07 hours_sleep=7 energy_level=7 joint_pain:=false

# Recomendación
http POST http://localhost:8000/api/training/recommendations/generate/ "Authorization: Bearer TOKEN" date=2026-03-07

# Workout log
http POST http://localhost:8000/api/training/workout-logs/ "Authorization: Bearer TOKEN" date=2026-03-07 video:=2 completed:=true rpe:=7
```

---

## 6. Seeds: catálogo Insanity

Cargar videos base (idempotente si no usas `--clear`):

```bash
cd backend
python manage.py seed_insanity_videos
```

Para reemplazar todos los videos del programa Insanity:

```bash
python manage.py seed_insanity_videos --clear
```

Videos incluidos: Cardio Recovery, Core Cardio and Balance, Plyometric Cardio Circuit, Cardio Power and Resistance, Pure Cardio, Max Interval Circuit, Max Interval Plyo, Max Cardio Conditioning.

---

## 7. Cómo probar localmente

1. **Entorno**
   - Python 3.11+ (o 3.9 con dependencias instaladas).
   - PostgreSQL accesible (por ejemplo con `DATABASE_URL` en `.env`).
   - `.env` con `OPENAI_API_KEY` (y opcionalmente `OPENAI_MODEL`, `OPENAI_TEMPERATURE`).

2. **Instalar y migrar**
   ```bash
   cd backend
   pip install -r requirements.txt
   python manage.py migrate
   python manage.py seed_insanity_videos
   ```

3. **Usuario**
   - Crear un usuario (admin o `createsuperuser` / registro) y obtener JWT con `POST /api/token/`.

4. **Flujo manual**
   - `POST /api/training/checkins/` con la fecha de hoy y tu estado.
   - `POST /api/training/recommendations/generate/` con `{"date": "YYYY-MM-DD"}`.
   - Revisar la recomendación; hacer el workout.
   - `POST /api/training/workout-logs/` con el video y feedback.
   - (Opcional) `POST /api/training/workout-feedback/analyze/` con `workout_log_id` o payload directo.

5. **Tests**
   - Con base de datos disponible (p. ej. PostgreSQL local):
     ```bash
     cd backend
     DJANGO_SETTINGS_MODULE=fitness_coach.settings python -m pytest apps/training/tests/ -v
     ```
   - Sin DB, los tests que usan `@pytest.mark.django_db` fallarán por conexión; el código de los tests es válido.

---

## 8. Próximos pasos

- **Frontend**: pantallas para check-in, recomendación del día, registro de workout y vista del análisis de feedback.
- **Notificaciones**: recordatorio para hacer check-in o ver la recomendación.
- **Historial**: listados de check-ins, recomendaciones y workout logs con filtros por fecha.
- **A/B o variantes**: probar distintos prompts o modelos (cambiando `OPENAI_MODEL`) y guardar versión en `TrainingRecommendation` o en metadata.
- **Métricas**: dashboards de adherencia, RPE medio, días de recovery vs intense.
- **Más programas**: ampliar `TrainingVideo` con más programas además de Insanity y reutilizar la misma lógica de readiness + candidatos + OpenAI.
