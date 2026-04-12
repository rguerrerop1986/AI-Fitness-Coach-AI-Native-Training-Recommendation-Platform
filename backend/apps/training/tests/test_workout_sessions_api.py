from datetime import date

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.training.models import WorkoutSession

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="session-user",
        email="session@example.com",
        password="testpass123",
        role=User.Role.CLIENT,
    )


@pytest.fixture
def other_user(db):
    return User.objects.create_user(
        username="session-other",
        email="session-other@example.com",
        password="testpass123",
        role=User.Role.CLIENT,
    )


@pytest.fixture
def api_client(user):
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return client


@pytest.mark.django_db
def test_workout_session_gym_flow_complete(api_client):
    create = api_client.post(
        "/api/training/workout-sessions/",
        {"session_date": date.today().isoformat(), "workout_type": "gym_workout"},
        format="json",
    )
    assert create.status_code == 201
    session_id = create.json()["id"]

    exercise = api_client.post(
        f"/api/training/workout-sessions/{session_id}/exercises/",
        {"exercise_name": "Bench Press"},
        format="json",
    )
    assert exercise.status_code == 201
    exercise_id = exercise.json()["id"]

    first_set = api_client.post(
        f"/api/training/workout-sessions/{session_id}/exercises/{exercise_id}/sets/",
        {"reps": 10, "weight_kg": "40.0"},
        format="json",
    )
    assert first_set.status_code == 201
    assert first_set.json()["set_number"] == 1

    second_set = api_client.post(
        f"/api/training/workout-sessions/{session_id}/exercises/{exercise_id}/sets/",
        {"reps": 8, "weight_kg": "50.0"},
        format="json",
    )
    assert second_set.status_code == 201
    assert second_set.json()["set_number"] == 2

    complete = api_client.post(f"/api/training/workout-sessions/{session_id}/complete/", {}, format="json")
    assert complete.status_code == 200
    payload = complete.json()
    assert payload["status"] == "completed"
    assert payload["total_exercises"] == 1
    assert payload["total_sets"] == 2
    assert payload["total_reps"] == 18
    assert float(payload["total_volume"]) == 800.0

    lock_edit = api_client.patch(
        f"/api/training/workout-sessions/{session_id}/",
        {"title": "Should fail"},
        format="json",
    )
    assert lock_edit.status_code == 400


@pytest.mark.django_db
def test_workout_session_ownership_enforced(api_client, other_user):
    foreign_session = WorkoutSession.objects.create(user=other_user, workout_type="video_workout")
    response = api_client.get(f"/api/training/workout-sessions/{foreign_session.id}/")
    assert response.status_code == 400
