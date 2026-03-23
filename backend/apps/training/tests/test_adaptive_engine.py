from datetime import date, timedelta

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.training.models import CompletedWorkout, DailyCheckIn, TrainingRecommendation
from apps.training.services.adaptive_recommendation_service import AdaptiveRecommendationService
from apps.training.services.readiness_service import ReadinessService

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="adaptive_user",
        email="adaptive@example.com",
        password="testpass123",
        role=User.Role.CLIENT,
    )


@pytest.fixture
def api_client(user):
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return client


def _checkin_payload(dt: date, **overrides):
    payload = {
        "date": dt,
        "sleep_quality": 8,
        "energy_level": 8,
        "motivation_level": 7,
        "muscle_soreness": 3,
        "stress_level": 3,
        "diet_adherence_yesterday": 8,
        "hydration_level": 8,
        "recovery_feeling": 8,
        "mental_clarity": 8,
        "workout_desire": 7,
    }
    payload.update(overrides)
    return payload


@pytest.mark.django_db
def test_daily_checkin_validation_range(user):
    checkin = DailyCheckIn(**_checkin_payload(date.today(), sleep_quality=11), user=user)
    with pytest.raises(Exception):
        checkin.full_clean()


@pytest.mark.django_db
def test_one_checkin_per_user_per_date(user):
    DailyCheckIn.objects.create(user=user, **_checkin_payload(date.today()))
    with pytest.raises(Exception):
        DailyCheckIn.objects.create(user=user, **_checkin_payload(date.today()))


@pytest.mark.django_db
def test_readiness_happy_path(user):
    checkin = DailyCheckIn.objects.create(user=user, **_checkin_payload(date.today()))
    analysis = ReadinessService().analyze(checkin)
    assert analysis.readiness_score >= 70
    assert analysis.readiness_band in {"good", "high"}


@pytest.mark.django_db
def test_penalty_alcohol(user):
    checkin = DailyCheckIn.objects.create(user=user, **_checkin_payload(date.today(), had_alcohol_yesterday=True))
    analysis = ReadinessService().analyze(checkin)
    assert any(p.code == "alcohol_yesterday" for p in analysis.penalties)


@pytest.mark.django_db
def test_penalty_injury(user):
    checkin = DailyCheckIn.objects.create(user=user, **_checkin_payload(date.today(), feels_pain_or_injury=True))
    analysis = ReadinessService().analyze(checkin)
    assert any(p.code == "pain_or_injury" for p in analysis.penalties)
    assert analysis.readiness_score <= 80


@pytest.mark.django_db
def test_penalty_poor_sleep(user):
    checkin = DailyCheckIn.objects.create(user=user, **_checkin_payload(date.today(), sleep_quality=4))
    analysis = ReadinessService().analyze(checkin)
    assert any(p.code == "sleep_very_low" for p in analysis.penalties)


@pytest.mark.django_db
def test_recommendation_high_readiness_hard(user):
    checkin = DailyCheckIn.objects.create(user=user, **_checkin_payload(date.today()))
    recommendation, _ = AdaptiveRecommendationService().generate_for_date(user, checkin.date)
    assert recommendation.recommendation_type in {
        TrainingRecommendation.RecommendationType.INSANITY_MAX,
        TrainingRecommendation.RecommendationType.STRENGTH_UPPER,
    }


@pytest.mark.django_db
def test_recommendation_high_stress_lighter(user):
    checkin = DailyCheckIn.objects.create(user=user, **_checkin_payload(date.today(), stress_level=9))
    recommendation, _ = AdaptiveRecommendationService().generate_for_date(user, checkin.date)
    assert recommendation.recommendation_type in {
        TrainingRecommendation.RecommendationType.CARDIO_LIGHT,
        TrainingRecommendation.RecommendationType.MOBILITY_RECOVERY,
    }


@pytest.mark.django_db
def test_recommendation_injury_rest(user):
    checkin = DailyCheckIn.objects.create(user=user, **_checkin_payload(date.today(), feels_pain_or_injury=True))
    recommendation, _ = AdaptiveRecommendationService().generate_for_date(user, checkin.date)
    assert recommendation.recommendation_type == TrainingRecommendation.RecommendationType.FULL_REST


@pytest.mark.django_db
def test_high_motivation_poor_recovery_prudent(user):
    checkin = DailyCheckIn.objects.create(
        user=user,
        **_checkin_payload(
            date.today(),
            motivation_level=9,
            sleep_quality=4,
            muscle_soreness=8,
        ),
    )
    recommendation, _ = AdaptiveRecommendationService().generate_for_date(user, checkin.date)
    assert recommendation.recommendation_type == TrainingRecommendation.RecommendationType.MOBILITY_RECOVERY


@pytest.mark.django_db
def test_api_generate_recommendation(api_client, user):
    DailyCheckIn.objects.create(user=user, **_checkin_payload(date.today()))
    response = api_client.post("/api/training/recommendations/generate/", {"date": date.today().isoformat()}, format="json")
    assert response.status_code == 200
    assert "readiness_score" in response.json()
    assert "recommendation_type" in response.json()


@pytest.mark.django_db
def test_recommendation_persistence_and_retrieval(api_client, user):
    DailyCheckIn.objects.create(user=user, **_checkin_payload(date.today()))
    api_client.post("/api/training/recommendations/generate/", {"date": date.today().isoformat()}, format="json")
    rec = TrainingRecommendation.objects.get(user=user, date=date.today())
    assert rec.readiness_score is not None

    today_response = api_client.get("/api/training/recommendations/today/")
    assert today_response.status_code == 200
    history_response = api_client.get("/api/training/recommendations/history/")
    assert history_response.status_code == 200
    assert len(history_response.json().get("results", [])) >= 1 or isinstance(history_response.json(), list)


@pytest.mark.django_db
def test_complete_workout_endpoint(api_client, user):
    checkin = DailyCheckIn.objects.create(user=user, **_checkin_payload(date.today()))
    rec, _ = AdaptiveRecommendationService().generate_for_date(user, checkin.date)
    response = api_client.post(
        "/api/training/workouts/complete/",
        {
            "recommendation": rec.id,
            "date": date.today().isoformat(),
            "workout_type": "insanity_max",
            "perceived_exertion": 8,
            "energy_after": 7,
            "satisfaction": 8,
            "completed": True,
            "notes": "Good session",
        },
        format="json",
    )
    assert response.status_code == 201
    assert CompletedWorkout.objects.filter(user=user, date=date.today()).exists()


@pytest.mark.django_db
def test_readiness_history_penalty_consecutive_hard_days(user):
    today = date.today()
    for i in range(1, 4):
        CompletedWorkout.objects.create(
            user=user,
            date=today - timedelta(days=i),
            workout_type="insanity_max",
            perceived_exertion=9,
            completed=True,
        )
    checkin = DailyCheckIn.objects.create(user=user, **_checkin_payload(today))
    analysis = ReadinessService().analyze(checkin)
    assert any(p.code == "three_consecutive_hard_days" for p in analysis.penalties)
