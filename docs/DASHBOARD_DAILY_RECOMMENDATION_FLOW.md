# Flujo de recomendación diaria automática — Dashboard cliente

## Resumen

El dashboard del cliente (`/client/dashboard`) consume **GET /api/client/dashboard/** y muestra automáticamente la recomendación del día (dieta + entrenamiento). El backend obtiene o crea la recomendación para la fecha actual y devuelve un payload consolidado. No se requieren migraciones nuevas (los modelos y constraints ya existían).

---

## 1. Archivos modificados

### Backend

| Archivo | Cambios |
|--------|---------|
| `backend/apps/client_portal/views.py` | `ClientDashboardView` ahora llama a `get_or_create_daily_recommendation(client, today)`, construye payload V2 con `_build_dashboard_v2_payload()` y devuelve `ClientDashboardV2Serializer`. Cliente expuesto con `height_cm` (convertido desde `height_m`). |
| `backend/apps/client_portal/serializers.py` | Añadidos `ClientDashboardV2Serializer`, `ClientDashboardClientSerializer`, `DietPlanActiveSerializer`, `DietPlanActiveMealSerializer`, `TrainingPlanActiveSerializer`, `TrainingPlanExerciseSerializer`, `TrainingPlanRecommendedVideoSerializer` para el payload del dashboard. |
| `backend/apps/client_portal/tests.py` | Test `test_client_dashboard_access` actualizado para estructura V2 (`client`, `today`, `diet_plan_active`, `training_plan_active`). Nueva clase `ClientDashboardDailyRecommendationTest` con 5 tests del flujo de recomendación diaria. |

### Frontend

| Archivo | Cambios |
|--------|---------|
| `frontend/src/pages/ClientDashboard.tsx` | Tipos alineados al payload V2 (`DashboardData`, `DashboardClient` con `height_cm`, etc.). `fetchClientData` definido con `useCallback` y usado en `useEffect` y en el botón "Reintentar". Cards de **dieta** (goal, calorías, comidas, mensaje coach) y **entrenamiento** (tipo, resumen, mensaje coach; video recomendado o lista de ejercicios). Estados: loading, error, empty. Uso de `client.height_cm` y `client.current_weight` (null-safe). |

---

## 2. Migraciones nuevas

**Ninguna.** Los modelos `DailyTrainingRecommendation`, `DailyTrainingRecommendationExercise`, `DailyDietRecommendation`, `DailyDietRecommendationMeal` y los constraints `(client, date)` ya existen en la migración `tracking/0010_daily_training_and_diet_recommendations.py`.

---

## 3. Endpoints actualizados

| Método | URL | Descripción |
|--------|-----|-------------|
| **GET** | `/api/client/dashboard/` | Devuelve payload V2: `client` (id, name, current_weight, height_cm), `today`, `diet_plan_active`, `training_plan_active`. Si no existe recomendación para hoy, la genera y persiste (idempotente por cliente y fecha). |

Requiere autenticación como cliente (`IsAuthenticated`, `IsClient`).

---

## 4. Ejemplo de response final

```json
{
  "client": {
    "id": 5,
    "name": "Sandy Gabriela",
    "current_weight": 61.0,
    "height_cm": 165
  },
  "today": "2026-03-09",
  "diet_plan_active": {
    "title": "Plan diario personalizado",
    "goal": "Definición ligera",
    "coach_message": "Mantén hidratación y distribuye proteína durante el día.",
    "total_calories": 1700,
    "meals": [
      { "meal_type": "breakfast", "title": "Desayuno alto en proteína" },
      { "meal_type": "lunch", "title": "Comida principal" },
      { "meal_type": "dinner", "title": "Cena" }
    ]
  },
  "training_plan_active": {
    "recommendation_type": "strength",
    "reasoning_summary": "Rutina equilibrada según tu nivel.",
    "coach_message": "Enfócate en técnica y control. Hidrátate bien.",
    "recommended_video": null,
    "exercises": [
      { "name": "Goblet Squat", "sets": 4, "reps": 12, "order": 1 }
    ]
  }
}
```

Si hay video recomendado en lugar de ejercicios:

```json
"training_plan_active": {
  "recommendation_type": "recovery",
  "reasoning_summary": "Priorizamos recuperación por fatiga o dolor reciente.",
  "coach_message": "Día de recuperación activa. Escucha a tu cuerpo.",
  "recommended_video": {
    "title": "Upper Body Strength 20 min",
    "duration_minutes": 20
  },
  "exercises": []
}
```

---

## 5. Pasos para probar el flujo

1. **Entorno**
   - Backend: `python manage.py runserver` (o tu comando habitual).
   - Frontend: `npm run dev` (o el que uses).
   - Base de datos con al menos un cliente vinculado a un usuario con `role=client` (ej. Sandy).

2. **Login como cliente**
   - Iniciar sesión con un usuario cliente (ej. Sandy) vía `/api/auth/token/client/` o desde el login del portal cliente.
   - Guardar el token (Bearer) en el frontend (ya lo hace tu flujo actual).

3. **Abrir dashboard**
   - Navegar a `/client/dashboard`.
   - Debe cargarse el dashboard con:
     - **Card de dieta:** goal, calorías, comidas principales, mensaje del coach.
     - **Card de entrenamiento:** tipo de recomendación, resumen, mensaje del coach y o bien **video recomendado** o bien **lista de ejercicios**.

4. **Idempotencia**
   - Refrescar la página una o más veces.
   - No deben crearse recomendaciones duplicadas (una por cliente y fecha).

5. **Comprobar en base de datos**
   - Para la fecha actual y el cliente usado:
     - `SELECT * FROM daily_training_recommendations WHERE client_id = X AND date = CURRENT_DATE;`
     - `SELECT * FROM daily_diet_recommendations WHERE client_id = X AND date = CURRENT_DATE;`
   - Debe haber como máximo una fila en cada tabla para ese cliente y fecha.

6. **Tests backend**
   - Ejecutar:
     - `python manage.py test apps.client_portal.tests.ClientPortalAPITest.test_client_dashboard_access`
     - `python manage.py test apps.client_portal.tests.ClientDashboardDailyRecommendationTest`

---

## Reglas aplicadas

- **Idempotencia:** constraint `(client, date)` en recomendaciones; `get_or_create_daily_recommendation` reutiliza la existente.
- **Persistencia:** ejercicios desde catálogo `Exercise`; video desde catálogo `TrainingVideo`.
- **N+1:** el servicio devuelve instancias con `select_related('recommended_video')` y `prefetch_related('exercises__exercise')` / `meals`; el payload se construye sin queries extra en bucle.
- **Datos faltantes:** `current_weight` y `height_cm` pueden ser `null`; el endpoint no rompe.
- **Altura:** todo expuesto en **height_cm** (convertido desde `height_m` en backend).
