"""Pytest configuration for training app. Ensures Django is configured when running from backend root."""
import os
import sys

# Ensure Django settings are used when running pytest (e.g. pytest apps/training/)
backend = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if backend not in sys.path:
    sys.path.insert(0, backend)
if not os.environ.get("DJANGO_SETTINGS_MODULE"):
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fitness_coach.settings")
