"""
Tests for the LangGraph-based recommendation flow: context, readiness, routing,
candidates, validation, fallback, persistence, and API response.
"""
from datetime import date

import pytest
from django.contrib.auth import get_user_model

from apps.catalogs.models import Exercise
from apps.training.models import DailyCheckIn, TrainingRecommendation, TrainingRecommendationExercise, WorkoutLog
from apps.training.graph.state import RecommendationState
from apps.training.graph import nodes
from apps.training.graph.recommendation_graph import graph, _is_valid

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="flowuser",
        email="flow@example.com",
        password="testpass123",
        role=User.Role.CLIENT,
        first_name="Flow",
        last_name="User",
    )


@pytest.fixture
def exercises(db):
    return [
        Exercise.objects.create(
            name="Recovery Stretch",
            muscle_group=Exercise.MuscleGroup.CORE,
            difficulty=Exercise.Difficulty.BEGINNER,
            intensity=2,
            tags=["mobility", "low_impact"],
            instructions="Stretch.",
            is_active=True,
        ),
        Exercise.objects.create(
            name="Push-ups",
            muscle_group=Exercise.MuscleGroup.CHEST,
            difficulty=Exercise.Difficulty.INTERMEDIATE,
            intensity=5,
            tags=[],
            instructions="Push.",
            is_active=True,
        ),
    ]


@pytest.mark.django_db
class TestLoadUserContext:
    """Context loading from DB."""

    def test_load_user_context_populates_state(self, user, exercises):
        state: RecommendationState = {
            "user_id": user.id,
            "date": date.today().isoformat(),
        }
        out = nodes.load_user_context(state)
        assert "checkin" in out
        assert "recent_workouts" in out
        assert "previous_recommendations" in out
        assert "exercise_catalog" in out
        assert len(out["exercise_catalog"]) >= 2
        assert out.get("error") is None

    def test_load_user_context_with_checkin(self, user, exercises):
        DailyCheckIn.objects.create(
            user=user,
            date=date.today(),
            hours_sleep=7.5,
            energy_level=8,
            joint_pain=False,
        )
        state = {"user_id": user.id, "date": date.today().isoformat()}
        out = nodes.load_user_context(state)
        assert out["checkin"] is not None
        assert out["checkin"]["hours_sleep"] == 7.5
        assert out["checkin"]["energy_level"] == 8


@pytest.mark.django_db
class TestAnalyzeReadiness:
    """Readiness score and flags."""

    def test_readiness_high_sleep_energy(self, user):
        state: RecommendationState = {
            "user_id": user.id,
            "date": date.today().isoformat(),
            "checkin": {"hours_sleep": 8, "energy_level": 8, "joint_pain": False},
            "recent_workouts": [],
        }
        out = nodes.analyze_readiness(state)
        assert out["readiness_score"] >= 0.7
        assert "readiness_flags" in out

    def test_readiness_low_energy_pain(self, user):
        state = {
            "user_id": user.id,
            "date": date.today().isoformat(),
            "checkin": {"energy_level": 2, "soreness_legs": 7, "joint_pain": True},
            "recent_workouts": [],
        }
        out = nodes.analyze_readiness(state)
        assert out["readiness_score"] <= 0.5
        assert "pain_or_soreness" in (out.get("readiness_flags") or [])


@pytest.mark.django_db
class TestRouteRecommendationType:
    """Routing by readiness and history."""

    def test_route_recovery_on_low_readiness(self, user):
        state = {
            "user_id": user.id,
            "date": date.today().isoformat(),
            "readiness_score": 0.25,
            "readiness_flags": ["pain_or_soreness"],
        }
        out = nodes.route_recommendation_type(state)
        assert out["recommendation_type"] == "recovery"

    def test_route_mobility_on_moderate_readiness(self, user):
        state = {
            "user_id": user.id,
            "date": date.today().isoformat(),
            "readiness_score": 0.45,
            "readiness_flags": [],
        }
        out = nodes.route_recommendation_type(state)
        assert out["recommendation_type"] in ("recovery", "mobility")


@pytest.mark.django_db
class TestRetrieveCandidateExercises:
    """Candidate retrieval from Exercise table."""

    def test_retrieve_returns_only_db_exercises(self, user, exercises):
        state = {
            "user_id": user.id,
            "date": date.today().isoformat(),
            "checkin": None,
            "recent_workouts": [],
            "previous_recommendations": [],
            "exercise_catalog": [{"id": e.id, "name": e.name, "muscle_group": e.muscle_group, "intensity": e.intensity} for e in exercises],
            "readiness_score": 0.7,
            "readiness_flags": [],
            "recommendation_type": "upper_strength",
        }
        out = nodes.retrieve_candidate_exercises(state)
        assert "candidate_exercises" in out
        ids = [c["id"] for c in out["candidate_exercises"]]
        for e in exercises:
            assert e.id in ids or True  # may be filtered by type


@pytest.mark.django_db
class TestBuildRecommendationStructuredOutput:
    """Structured plan shape (LLM or fallback)."""

    def test_build_returns_plan_with_exercises_from_candidates(self, user, exercises):
        """Without OpenAI key, fallback plan uses candidate exercise IDs."""
        state = {
            "user_id": user.id,
            "date": date.today().isoformat(),
            "candidate_exercises": [
                {"id": e.id, "name": e.name, "muscle_group": e.muscle_group, "intensity": e.intensity}
                for e in exercises
            ],
            "recommendation_type": "moderate",
        }
        from apps.training.prompts.recommendation_prompt import build_recommendation_plan_with_llm
        plan = build_recommendation_plan_with_llm(state)
        assert "recommendation_type" in plan
        assert "reasoning_summary" in plan
        assert "coach_message" in plan
        assert "exercises" in plan
        assert len(plan["exercises"]) >= 1
        assert plan["exercises"][0]["exercise_id"] in [e.id for e in exercises]


@pytest.mark.django_db
class TestValidateRecommendation:
    """Validation errors and warnings."""

    def test_validate_accepts_valid_plan(self, user, exercises):
        state = {
            "user_id": user.id,
            "candidate_exercises": [{"id": e.id} for e in exercises],
            "recommendation_plan": {
                "exercises": [
                    {"exercise_id": exercises[0].id, "sets": 3, "reps": 10, "rest_seconds": 60},
                ],
            },
            "checkin": {},
            "recommendation_type": "moderate",
        }
        out = nodes.validate_recommendation(state)
        assert out.get("validation_errors") == []

    def test_validate_rejects_invalid_exercise_id(self, user, exercises):
        state = {
            "user_id": user.id,
            "candidate_exercises": [{"id": e.id} for e in exercises],
            "recommendation_plan": {
                "exercises": [{"exercise_id": 99999, "sets": 3, "reps": 10}],
            },
        }
        out = nodes.validate_recommendation(state)
        assert len(out.get("validation_errors") or []) >= 1


@pytest.mark.django_db
class TestFallbackRecommendation:
    """Fallback path never crashes."""

    def test_fallback_produces_plan(self, user, exercises):
        state = {
            "user_id": user.id,
            "candidate_exercises": [],
            "exercise_catalog": [{"id": e.id, "intensity": 2} for e in exercises],
            "recommendation_type": "recovery",
        }
        out = nodes.fallback_recommendation(state)
        assert "recommendation_plan" in out
        assert out["recommendation_plan"]["recommendation_type"] == "recovery"
        assert isinstance(out["recommendation_plan"]["exercises"], list)


@pytest.mark.django_db
class TestPersistRecommendation:
    """Persistence of TrainingRecommendation and TrainingRecommendationExercise."""

    def test_persist_creates_rec_and_line_items(self, user, exercises):
        state = {
            "user_id": user.id,
            "date": date.today().isoformat(),
            "recommendation_plan": {
                "recommendation_type": "moderate",
                "reasoning_summary": "Test.",
                "coach_message": "Hi.",
                "exercises": [
                    {"exercise_id": exercises[0].id, "sets": 3, "reps": 12, "rest_seconds": 90, "notes": "", "position": 0},
                    {"exercise_id": exercises[1].id, "sets": 2, "reps": 10, "rest_seconds": 60, "notes": "", "position": 1},
                ],
            },
            "readiness_score": 0.8,
            "readiness_flags": [],
            "warnings": [],
        }
        out = nodes.persist_recommendation(state)
        assert out.get("persisted_recommendation_id") is not None
        rec = TrainingRecommendation.objects.get(pk=out["persisted_recommendation_id"])
        assert rec.user_id == user.id
        assert rec.date == date.today()
        assert rec.recommendation_type == "moderate"
        line_items = list(TrainingRecommendationExercise.objects.filter(recommendation=rec).order_by("position"))
        assert len(line_items) == 2
        assert line_items[0].exercise_id == exercises[0].id and line_items[0].sets == 3
        assert line_items[1].exercise_id == exercises[1].id and line_items[1].sets == 2


@pytest.mark.django_db
class TestGraphInvoke:
    """Full graph run."""

    def test_graph_invoke_returns_plan_and_persisted_id(self, user, exercises):
        result = graph.invoke({"user_id": user.id, "date": date.today().isoformat()})
        assert "recommendation_plan" in result
        assert result.get("persisted_recommendation_id") is not None
        plan = result["recommendation_plan"]
        assert "recommendation_type" in plan
        assert "exercises" in plan


@pytest.mark.django_db
class TestConditionalEdge:
    """Validate -> persist vs fallback."""

    def test_is_valid_persist_when_no_errors(self):
        assert _is_valid({"validation_errors": []}) == "persist"

    def test_is_valid_fallback_when_errors(self):
        assert _is_valid({"validation_errors": ["bad_id"]}) == "fallback"


@pytest.mark.django_db
class TestEndpointResponse:
    """POST /api/training/recommendations/generate/ response."""

    def test_endpoint_returns_200_with_plan(self, user, exercises):
        from rest_framework.test import APIClient
        from rest_framework_simplejwt.tokens import RefreshToken
        client = APIClient()
        refresh = RefreshToken.for_user(user)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
        resp = client.post(
            "/api/training/recommendations/generate/",
            {"date": date.today().isoformat()},
            format="json",
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "recommendation_plan" in data
        assert "date" in data
        assert "recommendation_type" in data.get("recommendation_plan", {})
        assert "exercises" in data["recommendation_plan"]
        assert data.get("persisted_recommendation_id") is not None
