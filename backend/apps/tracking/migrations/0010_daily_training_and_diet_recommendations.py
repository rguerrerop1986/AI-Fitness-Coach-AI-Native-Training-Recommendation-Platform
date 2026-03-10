# Daily training and diet recommendations for client dashboard

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0004_client_height_m_and_level'),
        ('catalogs', '0004_add_exercise_intensity_tags'),
        ('training', '0005_trainingvideo_url'),
        ('tracking', '0009_cooldown_last_tick_date'),
    ]

    operations = [
        migrations.CreateModel(
            name='DailyTrainingRecommendation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(db_index=True)),
                ('recommendation_type', models.CharField(
                    choices=[
                        ('strength', 'Strength'),
                        ('recovery', 'Recovery'),
                        ('mobility', 'Mobility'),
                        ('cardio', 'Cardio'),
                        ('core', 'Core'),
                        ('hiit', 'HIIT'),
                        ('full_body', 'Full Body'),
                        ('rest_day', 'Rest Day'),
                    ],
                    default='strength',
                    max_length=20,
                )),
                ('reasoning_summary', models.TextField(blank=True)),
                ('warnings', models.TextField(blank=True)),
                ('coach_message', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('client', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='daily_training_recommendations',
                    to='clients.client',
                )),
                ('recommended_video', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='daily_recommendations',
                    to='training.trainingvideo',
                )),
            ],
            options={
                'db_table': 'daily_training_recommendations',
                'ordering': ['-date', '-created_at'],
            },
        ),
        migrations.CreateModel(
            name='DailyDietRecommendation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(db_index=True)),
                ('title', models.CharField(blank=True, max_length=200)),
                ('goal', models.CharField(blank=True, max_length=100)),
                ('coach_message', models.TextField(blank=True)),
                ('reasoning_summary', models.TextField(blank=True)),
                ('total_calories', models.PositiveIntegerField(blank=True, null=True)),
                ('protein_g', models.PositiveIntegerField(blank=True, null=True)),
                ('carbs_g', models.PositiveIntegerField(blank=True, null=True)),
                ('fat_g', models.PositiveIntegerField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('client', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='daily_diet_recommendations',
                    to='clients.client',
                )),
            ],
            options={
                'db_table': 'daily_diet_recommendations',
                'ordering': ['-date', '-created_at'],
            },
        ),
        migrations.CreateModel(
            name='DailyTrainingRecommendationExercise',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.PositiveSmallIntegerField(default=0)),
                ('sets', models.PositiveSmallIntegerField(default=0)),
                ('reps', models.PositiveSmallIntegerField(default=0)),
                ('duration_minutes', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('rest_seconds', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('notes', models.TextField(blank=True)),
                ('exercise', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='daily_recommendation_line_items',
                    to='catalogs.exercise',
                )),
                ('recommendation', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='exercises',
                    to='tracking.dailytrainingrecommendation',
                )),
            ],
            options={
                'db_table': 'daily_training_recommendation_exercises',
                'ordering': ['recommendation', 'order'],
            },
        ),
        migrations.CreateModel(
            name='DailyDietRecommendationMeal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('meal_type', models.CharField(
                    choices=[
                        ('breakfast', 'Breakfast'),
                        ('lunch', 'Lunch'),
                        ('dinner', 'Dinner'),
                        ('snack', 'Snack'),
                        ('pre_workout', 'Pre-workout'),
                        ('post_workout', 'Post-workout'),
                    ],
                    max_length=20,
                )),
                ('title', models.CharField(blank=True, max_length=200)),
                ('description', models.TextField(blank=True)),
                ('calories', models.PositiveIntegerField(blank=True, null=True)),
                ('protein_g', models.PositiveIntegerField(blank=True, null=True)),
                ('carbs_g', models.PositiveIntegerField(blank=True, null=True)),
                ('fat_g', models.PositiveIntegerField(blank=True, null=True)),
                ('order', models.PositiveSmallIntegerField(default=0)),
                ('recommendation', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='meals',
                    to='tracking.dailydietrecommendation',
                )),
            ],
            options={
                'db_table': 'daily_diet_recommendation_meals',
                'ordering': ['recommendation', 'order'],
            },
        ),
        migrations.AddConstraint(
            model_name='dailytrainingrecommendation',
            constraint=models.UniqueConstraint(
                fields=('client', 'date'),
                name='daily_training_rec_client_date_unique',
            ),
        ),
        migrations.AddConstraint(
            model_name='dailydietrecommendation',
            constraint=models.UniqueConstraint(
                fields=('client', 'date'),
                name='daily_diet_rec_client_date_unique',
            ),
        ),
        migrations.AddIndex(
            model_name='dailytrainingrecommendation',
            index=models.Index(fields=['client', 'date'], name='daily_train_client__idx'),
        ),
        migrations.AddIndex(
            model_name='dailydietrecommendation',
            index=models.Index(fields=['client', 'date'], name='daily_diet__client__idx'),
        ),
    ]
