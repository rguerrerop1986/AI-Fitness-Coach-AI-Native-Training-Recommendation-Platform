# Daily exercise recommendation (V1 heuristic): one per client per date

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tracking', '0006_add_bmi_to_checkin'),
        ('clients', '0004_client_height_m_and_level'),
        ('catalogs', '0004_add_exercise_intensity_tags'),
    ]

    operations = [
        migrations.CreateModel(
            name='DailyExerciseRecommendation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(db_index=True)),
                ('intensity', models.CharField(
                    choices=[('low', 'Baja'), ('moderate', 'Moderada'), ('high', 'Alta')],
                    default='moderate',
                    max_length=20,
                )),
                ('type', models.CharField(
                    choices=[
                        ('mobility', 'Movilidad'),
                        ('cardio', 'Cardio'),
                        ('strength', 'Fuerza'),
                        ('core', 'Core'),
                        ('hiit', 'HIIT'),
                    ],
                    default='strength',
                    max_length=20,
                )),
                ('rationale', models.TextField(blank=True)),
                ('status', models.CharField(
                    choices=[
                        ('recommended', 'Recomendado'),
                        ('completed', 'Completado'),
                        ('skipped', 'Omitido'),
                    ],
                    default='recommended',
                    max_length=20,
                )),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('client', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='daily_exercise_recommendations',
                    to='clients.client',
                )),
                ('exercise', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='daily_recommendations',
                    to='catalogs.exercise',
                )),
            ],
            options={
                'db_table': 'daily_exercise_recommendations',
                'ordering': ['-date', '-created_at'],
            },
        ),
        migrations.AddConstraint(
            model_name='dailyexerciserecommendation',
            constraint=models.UniqueConstraint(
                fields=('client', 'date'),
                name='daily_ex_rec_client_date_unique',
            ),
        ),
    ]
