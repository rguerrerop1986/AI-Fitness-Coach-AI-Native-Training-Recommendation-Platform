"""
HTTP client for Fitness Coach Internal API.
Uses X-Internal-Token for auth. Base URL and token from env.
"""
import os
import httpx

BASE_URL = os.environ.get('FITNESS_API_BASE_URL', 'http://localhost:8000/api/internal')
INTERNAL_TOKEN = os.environ.get('INTERNAL_API_TOKEN', '')

DEFAULT_HEADERS = {
    'Content-Type': 'application/json',
    'X-Internal-Token': INTERNAL_TOKEN,
}


def _check_token():
    if not INTERNAL_TOKEN:
        raise ValueError('INTERNAL_API_TOKEN environment variable is required')


def _request(method: str, path: str, **kwargs) -> dict:
    _check_token()
    url = f"{BASE_URL.rstrip('/')}/{path.lstrip('/')}"
    headers = {**DEFAULT_HEADERS, **kwargs.pop('headers', {})}
    with httpx.Client(timeout=30.0) as client:
        resp = client.request(method, url, headers=headers, **kwargs)
        resp.raise_for_status()
        return resp.json() if resp.content else {}


def suggest_today(client_id: int, date_str: str | None = None) -> dict:
    """POST recommendations/suggest-today/"""
    payload = {'client_id': client_id}
    if date_str:
        payload['date'] = date_str
    return _request('POST', 'recommendations/suggest-today/', json=payload)


def get_training_context(client_id: int, days: int = 14) -> dict:
    """GET tracking/context/?client_id=&days="""
    params = {'client_id': client_id, 'days': days}
    return _request('GET', 'tracking/context/', params=params)


def record_feedback(
    client_id: int,
    date_str: str,
    execution_status: str,
    *,
    rpe: int | None = None,
    energy_level: int | None = None,
    pain_level: int | None = None,
    notes: str | None = None,
    executed_exercise_id: int | None = None,
) -> dict:
    """POST tracking/feedback/"""
    payload = {
        'client_id': client_id,
        'date': date_str,
        'execution_status': execution_status,
    }
    if rpe is not None:
        payload['rpe'] = rpe
    if energy_level is not None:
        payload['energy_level'] = energy_level
    if pain_level is not None:
        payload['pain_level'] = pain_level
    if notes is not None:
        payload['notes'] = notes
    if executed_exercise_id is not None:
        payload['executed_exercise_id'] = executed_exercise_id
    return _request('POST', 'tracking/feedback/', json=payload)


def coach_summary(coach_id: int, days: int = 7) -> dict:
    """GET coach/summary/?coach_id=&days="""
    params = {'coach_id': coach_id, 'days': days}
    return _request('GET', 'coach/summary/', params=params)


def list_exercises(query: str | None = None, tags: str | None = None, limit: int = 20) -> dict:
    """GET catalog/exercises/?q=&tags=&limit="""
    params = {'limit': limit}
    if query:
        params['q'] = query
    if tags:
        params['tags'] = tags
    return _request('GET', 'catalog/exercises/', params=params)
