# Dashboard: recomendaciones desde catálogo real

## Resumen

Las recomendaciones diarias de dieta y entrenamiento del dashboard del cliente se generan **solo** a partir del catálogo persistido (tablas `foods` y `exercises`). No se usan textos genéricos ni placeholders.

---

## 1. Archivos modificados

| Archivo | Cambios |
|---------|--------|
| `backend/apps/tracking/models.py` | Campo `training_group` en `DailyTrainingRecommendation`; nuevo modelo `DailyDietRecommendationMealFood` (meal FK, food FK, quantity, unit, order). |
| `backend/apps/tracking/migrations/0011_training_group_and_meal_foods.py` | Migración que añade `training_group` y crea la tabla `daily_diet_recommendation_meal_foods`. |
| `backend/apps/client_portal/services/daily_recommendation_service.py` | Dieta: generación desde `Food` (o desde ítems de plan activo); persistencia en `DailyDietRecommendationMeal` + `DailyDietRecommendationMealFood`. Entrenamiento: solo ejercicios del catálogo; cálculo y persistencia de `training_group`. Excepción `InsufficientCatalogError` cuando no hay suficientes alimentos o ejercicios. |
| `backend/apps/client_portal/views.py` | Payload de dieta con `meals[].foods[]` (id, name, quantity, unit, calories). Payload de entrenamiento con `training_group` y `training_group_label`. Manejo de 503 por `InsufficientCatalogError`. |
| `backend/apps/client_portal/serializers.py` | `DietPlanActiveMealSerializer` con `foods`; `DietPlanActiveFoodSerializer`; `TrainingPlanActiveSerializer` con `training_group`, `training_group_label`; ejercicios con `rest_seconds` y `notes`. |
| `frontend/src/pages/ClientDashboard.tsx` | Tipos para `DietFood`, `foods` en comidas, `training_group` / `training_group_label`. UI: comidas con lista de alimentos (nombre, cantidad, unidad, kcal); resumen y detalle con grupo de entrenamiento. Manejo de 503 por catálogo insuficiente. |
| `backend/apps/client_portal/tests.py` | SetUp con alimentos de catálogo; tests: dieta desde foods, sin títulos genéricos sin alimentos, entrenamiento desde exercises, training_group persistido y en response, 503 cuando faltan alimentos. |

---

## 2. Modelos

### DailyTrainingRecommendation

- **training_group** (CharField, blank=True): `upper_body`, `lower_body`, `core`, `insanity`, `full_body`, `active_recovery`.
- Se deriva de los `muscle_group` de los ejercicios (y tipo de recomendación / recuperación).

### DailyDietRecommendationMealFood

- **meal** → FK a `DailyDietRecommendationMeal`
- **food** → FK a `catalogs.Food`
- **quantity** (Decimal), **unit** (CharField, ej. `g`, `pieza`), **order** (PositiveSmallInteger).

---

## 3. Migraciones

- **0011_training_group_and_meal_foods**: añade `training_group` a `DailyTrainingRecommendation` y crea `DailyDietRecommendationMealFood`.

Aplicar:

```bash
cd backend && python manage.py migrate tracking
```

---

## 4. Serializers (payload)

**Dieta**

- `meals[]`: `meal_type`, `title`, `foods[]`.
- `foods[]`: `id`, `name`, `quantity`, `unit`, `calories` (opcional).

**Entrenamiento**

- `recommendation_type`, `training_group`, `training_group_label`, `reasoning_summary`, `coach_message`, `recommended_video`, `exercises[]`.
- `exercises[]`: `name`, `sets`, `reps`, `order`, `rest_seconds`, `notes`.

---

## 5. Ejemplo de response (GET /api/client/dashboard/)

```json
{
  "client": { "id": 1, "name": "Sandy Gabriela", "current_weight": 61, "height_cm": 165 },
  "today": "2025-03-09",
  "diet_plan_active": {
    "title": "Plan diario personalizado",
    "goal": "Mantenimiento",
    "coach_message": "Mantén hidratación y distribuye proteína durante el día.",
    "total_calories": 1800,
    "meals": [
      {
        "meal_type": "breakfast",
        "title": "Desayuno",
        "foods": [
          { "id": 12, "name": "Huevo", "quantity": 2, "unit": "pieza", "calories": 156 },
          { "id": 21, "name": "Avena", "quantity": 60, "unit": "g", "calories": 228 },
          { "id": 37, "name": "Plátano", "quantity": 1, "unit": "pieza", "calories": 105 }
        ]
      },
      {
        "meal_type": "lunch",
        "title": "Comida",
        "foods": [
          { "id": 5, "name": "Pechuga de pollo", "quantity": 150, "unit": "g", "calories": 248 },
          { "id": 8, "name": "Arroz", "quantity": 100, "unit": "g", "calories": 130 }
        ]
      },
      {
        "meal_type": "dinner",
        "title": "Cena",
        "foods": [
          { "id": 3, "name": "Atún", "quantity": 100, "unit": "g", "calories": 116 },
          { "id": 11, "name": "Aguacate", "quantity": 50, "unit": "g", "calories": 80 }
        ]
      }
    ]
  },
  "training_plan_active": {
    "recommendation_type": "strength",
    "training_group": "lower_body",
    "training_group_label": "Tren inferior",
    "reasoning_summary": "Rutina equilibrada según tu nivel.",
    "coach_message": "Enfócate en técnica y control. Hidrátate bien.",
    "recommended_video": null,
    "exercises": [
      { "name": "Goblet Squat", "sets": 3, "reps": 12, "order": 1, "rest_seconds": 60, "notes": "" }
    ]
  }
}
```

---

## 6. Cómo probar con Sandy

1. **Migraciones**
   ```bash
   cd backend && python manage.py migrate
   ```

2. **Catálogo**
   - Al menos **6 alimentos** activos en `foods` para poder generar dieta sin plan activo.
   - Al menos **2 ejercicios** activos (o al menos 1 video) para generar entrenamiento.

3. **Usuario cliente (Sandy)**
   - Cliente con `user` asociado y acceso al portal.
   - Opcional: PlanCycle activo con DietPlan que tenga comidas con ítems (MealItem → Food) para que la dieta diaria se derive del plan.

4. **Dashboard**
   - Login como Sandy → ir a `/client/dashboard` (o la ruta del dashboard).
   - Verificar:
     - **Dieta**: comidas con títulos (Desayuno, Comida, Cena) y lista de alimentos reales con cantidad y unidad.
     - **Entrenamiento**: Tipo, **Grupo** (ej. Tren inferior, Core, Reposo activo) y lista de ejercicios del catálogo.

5. **Catálogo insuficiente**
   - Si se borran o desactivan casi todos los alimentos y no hay plan con ítems, el GET al dashboard puede devolver **503** con `error: "insufficient_catalog"` y `catalog: "foods"`. El frontend muestra el mensaje de error (p. ej. “No hay suficientes alimentos en el catálogo…”).

---

## 7. Compatibilidad con datos antiguos

- Recomendaciones de dieta ya guardadas **sin** `DailyDietRecommendationMealFood`: se siguen leyendo; cada comida se muestra con su `title` y `foods: []`.
- Recomendaciones de entrenamiento **sin** `training_group`: el campo viene vacío; el frontend usa `recommendation_type` si no hay `training_group_label`.
- Las **nuevas** recomendaciones se guardan siempre con alimentos en `meal_foods` y con `training_group` cuando aplica.

---

## 8. Tests

En `backend/apps/client_portal/tests.py` (clase `ClientDashboardDailyRecommendationTest`):

- `test_diet_built_from_catalog_foods`: la dieta tiene al menos una comida con `foods` del catálogo.
- `test_diet_no_generic_placeholder_titles_only`: no se muestran solo títulos genéricos sin alimentos.
- `test_training_built_from_catalog_exercises`: los ejercicios vienen del catálogo.
- `test_training_group_persisted_and_returned`: `training_group` está en el modelo y en la respuesta.
- `test_dashboard_returns_training_group_label`: la respuesta incluye `training_group_label`.
- `test_insufficient_food_catalog_returns_503`: con pocos alimentos y sin plan con ítems, se responde 503 con `insufficient_catalog`.

Ejecutar:

```bash
cd backend && python manage.py test apps.client_portal.tests.ClientDashboardDailyRecommendationTest -v 2
```
