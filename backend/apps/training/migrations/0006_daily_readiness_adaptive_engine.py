from django.conf import settings
from django.db import migrations, models
import django.core.validators
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("training", "0005_trainingvideo_url"),
    ]

    operations = [
        migrations.AddField(
            model_name="dailycheckin",
            name="diet_adherence_yesterday",
            field=models.PositiveSmallIntegerField(
                blank=True,
                null=True,
                validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(10)],
            ),
        ),
        migrations.AddField(
            model_name="dailycheckin",
            name="feels_pain_or_injury",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="dailycheckin",
            name="had_alcohol_yesterday",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="dailycheckin",
            name="hydration_level",
            field=models.PositiveSmallIntegerField(
                blank=True,
                null=True,
                validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(10)],
            ),
        ),
        migrations.AddField(
            model_name="dailycheckin",
            name="mental_clarity",
            field=models.PositiveSmallIntegerField(
                blank=True,
                null=True,
                validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(10)],
            ),
        ),
        migrations.AddField(
            model_name="dailycheckin",
            name="muscle_soreness",
            field=models.PositiveSmallIntegerField(
                blank=True,
                null=True,
                validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(10)],
            ),
        ),
        migrations.AddField(
            model_name="dailycheckin",
            name="recovery_feeling",
            field=models.PositiveSmallIntegerField(
                blank=True,
                null=True,
                validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(10)],
            ),
        ),
        migrations.AddField(
            model_name="dailycheckin",
            name="stress_level",
            field=models.PositiveSmallIntegerField(
                blank=True,
                null=True,
                validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(10)],
            ),
        ),
        migrations.AddField(
            model_name="dailycheckin",
            name="wants_insanity_today",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="dailycheckin",
            name="wants_recovery_today",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="dailycheckin",
            name="wants_strength_today",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="dailycheckin",
            name="workout_desire",
            field=models.PositiveSmallIntegerField(
                blank=True,
                null=True,
                validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(10)],
            ),
        ),
        migrations.CreateModel(
            name="CompletedWorkout",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("date", models.DateField(db_index=True)),
                ("workout_type", models.CharField(max_length=32)),
                (
                    "perceived_exertion",
                    models.PositiveSmallIntegerField(
                        blank=True,
                        null=True,
                        validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(10)],
                    ),
                ),
                (
                    "energy_after",
                    models.PositiveSmallIntegerField(
                        blank=True,
                        null=True,
                        validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(10)],
                    ),
                ),
                (
                    "satisfaction",
                    models.PositiveSmallIntegerField(
                        blank=True,
                        null=True,
                        validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(10)],
                    ),
                ),
                ("completed", models.BooleanField(default=True)),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "recommendation",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="completed_workouts",
                        to="training.trainingrecommendation",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="completed_workouts",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "training_completed_workouts",
                "ordering": ["-date", "-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="completedworkout",
            index=models.Index(fields=["user", "date"], name="training_com_user_id_31d3ff_idx"),
        ),
        migrations.AddField(
            model_name="trainingrecommendation",
            name="checkin",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="recommendations",
                to="training.dailycheckin",
            ),
        ),
        migrations.AddField(
            model_name="trainingrecommendation",
            name="duration_minutes",
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="trainingrecommendation",
            name="intensity_level",
            field=models.CharField(
                choices=[("low", "Low"), ("moderate", "Moderate"), ("high", "High"), ("recovery", "Recovery")],
                default="moderate",
                max_length=12,
            ),
        ),
        migrations.AlterField(
            model_name="trainingrecommendation",
            name="warnings",
            field=models.JSONField(blank=True, default=list),
        ),
    ]
