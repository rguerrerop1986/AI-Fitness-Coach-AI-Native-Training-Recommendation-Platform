# Generated for recommendation engine: readiness_score, metadata, TrainingRecommendationExercise

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('catalogs', '0004_add_exercise_intensity_tags'),
        ('training', '0003_trainingrecommendation_recommended_exercise'),
    ]

    operations = [
        migrations.AddField(
            model_name='trainingrecommendation',
            name='readiness_score',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='trainingrecommendation',
            name='metadata',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AlterField(
            model_name='trainingrecommendation',
            name='recommendation_type',
            field=models.CharField(
                choices=[
                    ('recovery', 'Recovery'),
                    ('light', 'Light'),
                    ('moderate', 'Moderate'),
                    ('intense', 'Intense'),
                    ('max', 'Max'),
                    ('mobility', 'Mobility'),
                    ('upper_strength', 'Upper Strength'),
                    ('lower_strength', 'Lower Strength'),
                    ('cardio', 'Cardio'),
                    ('full_body', 'Full Body'),
                    ('rest_day', 'Rest Day'),
                ],
                default='moderate',
                max_length=24,
            ),
        ),
        migrations.CreateModel(
            name='TrainingRecommendationExercise',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sets', models.PositiveSmallIntegerField(default=0)),
                ('reps', models.PositiveSmallIntegerField(default=0)),
                ('rest_seconds', models.PositiveSmallIntegerField(default=0)),
                ('notes', models.TextField(blank=True)),
                ('position', models.PositiveSmallIntegerField(default=0)),
                ('exercise', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='recommendation_line_items',
                    to='catalogs.exercise',
                )),
                ('recommendation', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='recommended_exercises',
                    to='training.trainingrecommendation',
                )),
            ],
            options={
                'db_table': 'training_recommendation_exercises',
                'ordering': ['recommendation', 'position'],
            },
        ),
    ]
