"""
Seed base exercises for daily recommendation (V1 catalog by level).
Creates exercises with tags/difficulty so generate_daily_recommendation can pick them.
Run: python manage.py seed_daily_exercise_catalog
"""
from django.core.management.base import BaseCommand
from apps.catalogs.models import Exercise


BASE_EXERCISES = [
    # Beginner: mobility, low impact, core
    {'name': 'Movilidad articular 10 min', 'muscle_group': 'other', 'difficulty': 'beginner', 'intensity': 2, 'tags': ['mobility', 'low_impact', 'no-impact'], 'instructions': 'Calentamiento articular suave: cuello, hombros, cadera, rodillas.'},
    {'name': 'Caminata ligera 20 min', 'muscle_group': 'cardio', 'difficulty': 'beginner', 'intensity': 3, 'tags': ['cardio', 'low_impact'], 'instructions': 'Caminata a ritmo cómodo, mantén frecuencia cardíaca moderada.'},
    {'name': 'Core básico (plancha y abdominales)', 'muscle_group': 'core', 'difficulty': 'beginner', 'intensity': 4, 'tags': ['core', 'low_impact'], 'instructions': 'Plancha 20s x 3, abdominales crunch 10 x 3.'},
    {'name': 'Estiramiento y movilidad 15 min', 'muscle_group': 'other', 'difficulty': 'beginner', 'intensity': 2, 'tags': ['mobility', 'low_impact', 'no-impact'], 'instructions': 'Estiramientos estáticos de piernas, espalda y brazos.'},
    {'name': 'Bici estática suave 15 min', 'muscle_group': 'cardio', 'difficulty': 'beginner', 'intensity': 3, 'tags': ['cardio', 'low_impact', 'knee-friendly'], 'instructions': 'Pedaleo suave sin resistencia alta.'},
    # Intermediate
    {'name': 'Circuito cuerpo completo moderado', 'muscle_group': 'full_body', 'difficulty': 'intermediate', 'intensity': 5, 'tags': ['strength', 'cardio'], 'instructions': '4 ejercicios x 3 rondas: sentadillas, flexiones, remo, plancha.'},
    {'name': 'HIIT moderado 20 min', 'muscle_group': 'cardio', 'difficulty': 'intermediate', 'intensity': 6, 'tags': ['hiit', 'cardio'], 'instructions': '30s trabajo / 30s descanso x 8 ejercicios.'},
    {'name': 'Core intermedio', 'muscle_group': 'core', 'difficulty': 'intermediate', 'intensity': 5, 'tags': ['core'], 'instructions': 'Plancha, mountain climbers, hollow hold.'},
    {'name': 'Fuerza tren inferior', 'muscle_group': 'quads', 'difficulty': 'intermediate', 'intensity': 5, 'tags': ['strength'], 'instructions': 'Sentadillas, zancadas, peso muerto rumano.'},
    {'name': 'Cardio steady 25 min', 'muscle_group': 'cardio', 'difficulty': 'intermediate', 'intensity': 5, 'tags': ['cardio'], 'instructions': 'Correr o bici a ritmo constante.'},
    # Advanced
    {'name': 'HIIT intenso 25 min', 'muscle_group': 'cardio', 'difficulty': 'advanced', 'intensity': 8, 'tags': ['hiit', 'cardio'], 'instructions': '40s trabajo / 20s descanso x 10 ejercicios.'},
    {'name': 'Fuerza alta volumen', 'muscle_group': 'full_body', 'difficulty': 'advanced', 'intensity': 7, 'tags': ['strength'], 'instructions': 'Press banca, sentadilla, peso muerto, remo.'},
    {'name': 'Core avanzado', 'muscle_group': 'core', 'difficulty': 'advanced', 'intensity': 6, 'tags': ['core'], 'instructions': 'Plancha con desplazamiento, dragon flag progresión.'},
    {'name': 'Recuperación movilidad', 'muscle_group': 'other', 'difficulty': 'advanced', 'intensity': 2, 'tags': ['mobility', 'low_impact', 'no-impact'], 'instructions': 'Movilidad y estiramiento post-entreno.'},
    {'name': 'Sprint intervals', 'muscle_group': 'cardio', 'difficulty': 'advanced', 'intensity': 9, 'tags': ['hiit', 'cardio'], 'instructions': '8 x 30s sprint / 90s descanso.'},
]


class Command(BaseCommand):
    help = 'Seed base exercises for daily recommendation (by level + tags).'

    def handle(self, *args, **options):
        created = 0
        for data in BASE_EXERCISES:
            _, was_created = Exercise.objects.get_or_create(
                name=data['name'],
                defaults={
                    'muscle_group': data['muscle_group'],
                    'difficulty': data['difficulty'],
                    'intensity': data['intensity'],
                    'tags': data['tags'],
                    'instructions': data['instructions'],
                },
            )
            if was_created:
                created += 1
        self.stdout.write(self.style.SUCCESS(f'Created {created} new exercises; {len(BASE_EXERCISES) - created} already existed.'))
