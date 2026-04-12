from django.conf import settings
from django.db import migrations, models
import django.core.validators
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        ("training", "0006_daily_readiness_adaptive_engine"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="WorkoutSession",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("session_date", models.DateField(db_index=True, default=django.utils.timezone.localdate)),
                (
                    "workout_type",
                    models.CharField(
                        choices=[("video_workout", "Video Workout"), ("gym_workout", "Gym Workout")],
                        default="video_workout",
                        max_length=20,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[("in_progress", "In Progress"), ("completed", "Completed")],
                        default="in_progress",
                        max_length=20,
                    ),
                ),
                ("title", models.CharField(blank=True, max_length=200)),
                ("video_name", models.CharField(blank=True, max_length=200)),
                ("notes", models.TextField(blank=True)),
                ("ai_summary", models.TextField(blank=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("total_exercises", models.PositiveIntegerField(default=0)),
                ("total_sets", models.PositiveIntegerField(default=0)),
                ("total_reps", models.PositiveIntegerField(default=0)),
                ("total_volume", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="training_workout_sessions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "training_workout_sessions",
                "ordering": ["-session_date", "-created_at"],
                "indexes": [models.Index(fields=["user", "session_date"], name="training_wo_user_id_4202a8_idx")],
            },
        ),
        migrations.CreateModel(
            name="WorkoutExercise",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("exercise_name", models.CharField(max_length=200)),
                ("order", models.PositiveSmallIntegerField(default=1)),
                ("notes", models.TextField(blank=True)),
                (
                    "intensity",
                    models.PositiveSmallIntegerField(
                        blank=True,
                        null=True,
                        validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(10)],
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "workout_session",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="exercises",
                        to="training.workoutsession",
                    ),
                ),
            ],
            options={
                "db_table": "training_workout_exercises",
                "ordering": ["order", "id"],
                "indexes": [models.Index(fields=["workout_session", "order"], name="training_wo_workout_0e6ffb_idx")],
            },
        ),
        migrations.CreateModel(
            name="ExerciseSet",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("set_number", models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1)])),
                ("reps", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("weight_kg", models.DecimalField(blank=True, decimal_places=2, max_digits=7, null=True)),
                (
                    "intensity",
                    models.PositiveSmallIntegerField(
                        blank=True,
                        null=True,
                        validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(10)],
                    ),
                ),
                ("rest_seconds", models.PositiveIntegerField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "workout_exercise",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="sets",
                        to="training.workoutexercise",
                    ),
                ),
            ],
            options={
                "db_table": "training_exercise_sets",
                "ordering": ["set_number", "id"],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("workout_exercise", "set_number"),
                        name="training_exercise_sets_exercise_set_number_unique",
                    )
                ],
            },
        ),
    ]
