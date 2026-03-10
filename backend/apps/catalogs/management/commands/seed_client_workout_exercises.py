"""
Seed client-specific workout exercises into catalogs.Exercise.

Idempotent: uses get_or_create(name=...) so it can be run multiple times
without duplicar ejercicios. This enriches the catalog with common gym
and Insanity-style entries used by the daily recommendation engine.
"""
from django.core.management.base import BaseCommand

from apps.catalogs.models import Exercise


CLIENT_EXERCISES = [
    # --- Fuerza tren superior ---
    {
        'name': 'Press Militar con Mancuernas',
        'muscle_group': Exercise.MuscleGroup.SHOULDERS,
        'equipment_type': Exercise.EquipmentType.MANCUERNA,
        'difficulty': Exercise.Difficulty.INTERMEDIATE,
        'intensity': 6,
        'tags': ['strength', 'upper_body'],
        'instructions': 'Press militar de pie o sentado con mancuernas, controlando el movimiento.',
    },
    {
        'name': 'Elevaciones Laterales',
        'muscle_group': Exercise.MuscleGroup.SHOULDERS,
        'equipment_type': Exercise.EquipmentType.MANCUERNA,
        'difficulty': Exercise.Difficulty.BEGINNER,
        'intensity': 5,
        'tags': ['strength', 'upper_body'],
        'instructions': 'Elevaciones laterales de hombro con mancuernas, sin balanceo.',
    },
    {
        'name': 'Bench Press con Barra',
        'muscle_group': Exercise.MuscleGroup.CHEST,
        'equipment_type': Exercise.EquipmentType.BARRA,
        'difficulty': Exercise.Difficulty.INTERMEDIATE,
        'intensity': 7,
        'tags': ['strength', 'upper_body'],
        'instructions': 'Press de banca con barra, pies firmes y control de la barra.',
    },
    {
        'name': 'Push Up',
        'muscle_group': Exercise.MuscleGroup.CHEST,
        'equipment_type': Exercise.EquipmentType.PESO_CORPORAL,
        'difficulty': Exercise.Difficulty.BEGINNER,
        'intensity': 5,
        'tags': ['strength', 'upper_body', 'peso_corporal'],
        'instructions': 'Flexiones de pecho con cuerpo alineado y core activo.',
    },
    {
        'name': 'Curl Bíceps con Mancuernas',
        'muscle_group': Exercise.MuscleGroup.BICEPS,
        'equipment_type': Exercise.EquipmentType.MANCUERNA,
        'difficulty': Exercise.Difficulty.BEGINNER,
        'intensity': 5,
        'tags': ['strength', 'upper_body'],
        'instructions': 'Curl de bíceps alterno o simultáneo con mancuernas.',
    },
    {
        'name': 'Curl Martillo',
        'muscle_group': Exercise.MuscleGroup.BICEPS,
        'equipment_type': Exercise.EquipmentType.MANCUERNA,
        'difficulty': Exercise.Difficulty.BEGINNER,
        'intensity': 5,
        'tags': ['strength', 'upper_body'],
        'instructions': 'Curl de bíceps agarre neutro (martillo) con mancuernas.',
    },
    {
        'name': 'Pájaros con Mancuernas',
        'muscle_group': Exercise.MuscleGroup.SHOULDERS,
        'equipment_type': Exercise.EquipmentType.MANCUERNA,
        'difficulty': Exercise.Difficulty.INTERMEDIATE,
        'intensity': 6,
        'tags': ['strength', 'upper_body'],
        'instructions': 'Elevaciones posteriores para deltoides posterior con ligera inclinación.',
    },
    {
        'name': 'Copa Tríceps con Mancuerna',
        'muscle_group': Exercise.MuscleGroup.TRICEPS,
        'equipment_type': Exercise.EquipmentType.MANCUERNA,
        'difficulty': Exercise.Difficulty.BEGINNER,
        'intensity': 5,
        'tags': ['strength', 'upper_body'],
        'instructions': 'Extensión de tríceps por encima de la cabeza con mancuerna.',
    },
    {
        'name': 'Tríceps en Polea',
        'muscle_group': Exercise.MuscleGroup.TRICEPS,
        'equipment_type': Exercise.EquipmentType.CABLE,
        'difficulty': Exercise.Difficulty.INTERMEDIATE,
        'intensity': 6,
        'tags': ['strength', 'upper_body', 'machine'],
        'instructions': 'Extensiones de tríceps en polea alta con agarre cómodo.',
    },
    {
        'name': 'Press Inclinado con Mancuernas',
        'muscle_group': Exercise.MuscleGroup.CHEST,
        'equipment_type': Exercise.EquipmentType.MANCUERNA,
        'difficulty': Exercise.Difficulty.INTERMEDIATE,
        'intensity': 6,
        'tags': ['strength', 'upper_body'],
        'instructions': 'Press de pecho inclinado con mancuernas, énfasis en parte superior.',
    },
    {
        'name': 'Elevaciones Frontales',
        'muscle_group': Exercise.MuscleGroup.SHOULDERS,
        'equipment_type': Exercise.EquipmentType.MANCUERNA,
        'difficulty': Exercise.Difficulty.BEGINNER,
        'intensity': 5,
        'tags': ['strength', 'upper_body'],
        'instructions': 'Elevación frontal de hombro con mancuernas a altura de ojos.',
    },
    {
        'name': 'Lat Pulldown',
        'muscle_group': Exercise.MuscleGroup.BACK,
        'equipment_type': Exercise.EquipmentType.MAQUINA,
        'difficulty': Exercise.Difficulty.BEGINNER,
        'intensity': 5,
        'tags': ['strength', 'upper_body', 'machine'],
        'instructions': 'Jalón al pecho en polea, enfocado en dorsales.',
    },
    {
        'name': 'Chest Press en Máquina',
        'muscle_group': Exercise.MuscleGroup.CHEST,
        'equipment_type': Exercise.EquipmentType.MAQUINA,
        'difficulty': Exercise.Difficulty.BEGINNER,
        'intensity': 5,
        'tags': ['strength', 'upper_body', 'machine'],
        'instructions': 'Press de pecho en máquina guiada.',
    },
    {
        'name': 'Pec Fly',
        'muscle_group': Exercise.MuscleGroup.CHEST,
        'equipment_type': Exercise.EquipmentType.MAQUINA,
        'difficulty': Exercise.Difficulty.BEGINNER,
        'intensity': 5,
        'tags': ['strength', 'upper_body', 'machine'],
        'instructions': 'Aperturas de pecho en máquina o con mancuernas.',
    },
    # --- Tren inferior / máquinas ---
    {
        'name': 'MTS Row',
        'muscle_group': Exercise.MuscleGroup.BACK,
        'equipment_type': Exercise.EquipmentType.MAQUINA,
        'difficulty': Exercise.Difficulty.INTERMEDIATE,
        'intensity': 6,
        'tags': ['strength', 'upper_body', 'machine'],
        'instructions': 'Remo en máquina MTS para espalda media.',
    },
    # --- Core / abdomen ---
    {
        'name': 'Crunch en el Suelo',
        'muscle_group': Exercise.MuscleGroup.CORE,
        'equipment_type': Exercise.EquipmentType.PESO_CORPORAL,
        'difficulty': Exercise.Difficulty.BEGINNER,
        'intensity': 4,
        'tags': ['core'],
        'instructions': 'Crunch abdominal en el suelo con control de respiración.',
    },
    {
        'name': 'Plancha (Plank)',
        'muscle_group': Exercise.MuscleGroup.CORE,
        'equipment_type': Exercise.EquipmentType.PESO_CORPORAL,
        'difficulty': Exercise.Difficulty.BEGINNER,
        'intensity': 4,
        'tags': ['core', 'low_impact'],
        'instructions': 'Plancha isométrica apoyado en antebrazos y puntas de pies.',
    },
    {
        'name': 'Elevate Core',
        'muscle_group': Exercise.MuscleGroup.CORE,
        'equipment_type': Exercise.EquipmentType.MAQUINA,
        'difficulty': Exercise.Difficulty.INTERMEDIATE,
        'intensity': 6,
        'tags': ['core', 'machine'],
        'instructions': 'Trabajo de core en máquina Elevate u opción similar.',
    },
    {
        'name': 'Abdominal Hammer',
        'muscle_group': Exercise.MuscleGroup.CORE,
        'equipment_type': Exercise.EquipmentType.MAQUINA,
        'difficulty': Exercise.Difficulty.INTERMEDIATE,
        'intensity': 6,
        'tags': ['core', 'machine'],
        'instructions': 'Crunch abdominal en máquina tipo Hammer.',
    },
    {
        'name': 'Rotary Torso',
        'muscle_group': Exercise.MuscleGroup.CORE,
        'equipment_type': Exercise.EquipmentType.MAQUINA,
        'difficulty': Exercise.Difficulty.BEGINNER,
        'intensity': 4,
        'tags': ['core', 'machine'],
        'instructions': 'Rotación controlada de tronco en máquina Rotary Torso.',
    },
    # --- Cardio / máquinas (reposo activo) ---
    {
        'name': 'Elíptica',
        'muscle_group': Exercise.MuscleGroup.CARDIO,
        'equipment_type': Exercise.EquipmentType.MAQUINA,
        'difficulty': Exercise.Difficulty.BEGINNER,
        'intensity': 3,
        'tags': ['cardio', 'machine', 'low_impact', 'warmup'],
        'instructions': 'Cardio suave en elíptica, ritmo cómodo.',
    },
    {
        'name': 'Climb Mill',
        'muscle_group': Exercise.MuscleGroup.CARDIO,
        'equipment_type': Exercise.EquipmentType.MAQUINA,
        'difficulty': Exercise.Difficulty.INTERMEDIATE,
        'intensity': 4,
        'tags': ['cardio', 'machine', 'low_impact'],
        'instructions': 'Subida de escalera en máquina tipo Climb Mill.',
    },
    # --- Insanity-style videos como ejercicios de catálogo ---
    {
        'name': 'Plyometric Cardio Circuit',
        'muscle_group': Exercise.MuscleGroup.FULL_BODY,
        'equipment_type': Exercise.EquipmentType.PESO_CORPORAL,
        'difficulty': Exercise.Difficulty.ADVANCED,
        'intensity': 8,
        'tags': ['insanity', 'video', 'full_body', 'hiit', 'cardio'],
        'instructions': 'Circuito pliométrico estilo Insanity.',
    },
    {
        'name': 'Cardio Recovery',
        'muscle_group': Exercise.MuscleGroup.CARDIO,
        'equipment_type': Exercise.EquipmentType.PESO_CORPORAL,
        'difficulty': Exercise.Difficulty.INTERMEDIATE,
        'intensity': 4,
        'tags': ['insanity', 'video', 'cardio', 'recovery', 'low_impact'],
        'instructions': 'Sesión de cardio recovery estilo Insanity.',
    },
    {
        'name': 'Pure Cardio',
        'muscle_group': Exercise.MuscleGroup.CARDIO,
        'equipment_type': Exercise.EquipmentType.PESO_CORPORAL,
        'difficulty': Exercise.Difficulty.ADVANCED,
        'intensity': 8,
        'tags': ['insanity', 'video', 'cardio', 'hiit'],
        'instructions': 'Sesión Pure Cardio estilo Insanity.',
    },
    {
        'name': 'Core Cardio & Balance',
        'muscle_group': Exercise.MuscleGroup.FULL_BODY,
        'equipment_type': Exercise.EquipmentType.PESO_CORPORAL,
        'difficulty': Exercise.Difficulty.INTERMEDIATE,
        'intensity': 6,
        'tags': ['insanity', 'video', 'core', 'cardio', 'full_body'],
        'instructions': 'Core Cardio & Balance estilo Insanity.',
    },
    {
        'name': 'Max Recovery',
        'muscle_group': Exercise.MuscleGroup.FULL_BODY,
        'equipment_type': Exercise.EquipmentType.PESO_CORPORAL,
        'difficulty': Exercise.Difficulty.INTERMEDIATE,
        'intensity': 4,
        'tags': ['insanity', 'video', 'recovery', 'full_body', 'low_impact'],
        'instructions': 'Sesión Max Recovery estilo Insanity.',
    },
    {
        'name': 'Max Interval Circuit',
        'muscle_group': Exercise.MuscleGroup.FULL_BODY,
        'equipment_type': Exercise.EquipmentType.PESO_CORPORAL,
        'difficulty': Exercise.Difficulty.ADVANCED,
        'intensity': 9,
        'tags': ['insanity', 'video', 'full_body', 'hiit'],
        'instructions': 'Max Interval Circuit estilo Insanity.',
    },
    {
        'name': 'Max Cardio Conditioning',
        'muscle_group': Exercise.MuscleGroup.CARDIO,
        'equipment_type': Exercise.EquipmentType.PESO_CORPORAL,
        'difficulty': Exercise.Difficulty.ADVANCED,
        'intensity': 9,
        'tags': ['insanity', 'video', 'cardio', 'hiit'],
        'instructions': 'Max Cardio Conditioning estilo Insanity.',
    },
    {
        'name': 'Max Interval Plyo',
        'muscle_group': Exercise.MuscleGroup.FULL_BODY,
        'equipment_type': Exercise.EquipmentType.PESO_CORPORAL,
        'difficulty': Exercise.Difficulty.ADVANCED,
        'intensity': 9,
        'tags': ['insanity', 'video', 'full_body', 'hiit'],
        'instructions': 'Max Interval Plyo estilo Insanity.',
    },
    {
        'name': 'Upper Body Weight Training',
        'muscle_group': Exercise.MuscleGroup.FULL_BODY,
        'equipment_type': Exercise.EquipmentType.MANCUERNA,
        'difficulty': Exercise.Difficulty.ADVANCED,
        'intensity': 8,
        'tags': ['insanity', 'video', 'upper_body', 'full_body', 'strength'],
        'instructions': 'Upper Body Weight Training estilo Insanity.',
    },
]


class Command(BaseCommand):
    help = 'Seed client workout exercises into catalogs.Exercise (idempotent).'

    def handle(self, *args, **options):
        created = 0
        for data in CLIENT_EXERCISES:
            name = data['name']
            defaults = {
                'muscle_group': data['muscle_group'],
                'difficulty': data['difficulty'],
                'intensity': data['intensity'],
                'instructions': data['instructions'],
                'is_active': True,
                'tags': data.get('tags', []),
            }
            if data.get('equipment_type'):
                defaults['equipment_type'] = data['equipment_type']
            obj, was_created = Exercise.objects.get_or_create(
                name=name,
                defaults=defaults,
            )
            if was_created:
                created += 1
            else:
                # Opcional: actualizar campos clave sin romper overrides manuales
                updated = False
                for field, value in defaults.items():
                    if getattr(obj, field) in (None, [], ''):
                        setattr(obj, field, value)
                        updated = True
                if updated:
                    obj.save(update_fields=list(defaults.keys()) + ['updated_at'])
        self.stdout.write(
            self.style.SUCCESS(
                f'Client workout exercises seeding complete. Created {created} new exercises; '
                f'{len(CLIENT_EXERCISES) - created} already existed.'
            )
        )

