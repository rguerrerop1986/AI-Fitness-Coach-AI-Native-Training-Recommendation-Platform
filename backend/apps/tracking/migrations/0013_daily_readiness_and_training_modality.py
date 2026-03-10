# DailyReadinessCheckin + modality/intensity_level on DailyTrainingRecommendation

from django.db import migrations, models
import django.db.models.deletion
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0006_alter_client_height_m_alter_client_level'),
        ('tracking', '0012_rename_daily_diet__client__idx_daily_diet__client__a8a165_idx_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='DailyReadinessCheckin',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(db_index=True)),
                ('sleep_quality', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('diet_adherence_yesterday', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('motivation_today', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('energy_level', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('stress_level', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('muscle_soreness', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('readiness_to_train', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('mood', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('hydration_level', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('yesterday_training_intensity', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('slept_poorly', models.BooleanField(default=False)),
                ('ate_poorly_yesterday', models.BooleanField(default=False)),
                ('feels_100_percent', models.BooleanField(default=False)),
                ('wants_video_today', models.BooleanField(default=False)),
                ('preferred_training_mode', models.CharField(
                    choices=[
                        ('insanity', 'Insanity'),
                        ('hybrid', 'Hybrid'),
                        ('gym_strength', 'Gym Strength'),
                        ('mobility_recovery', 'Mobility Recovery'),
                        ('auto', 'Auto'),
                    ],
                    default='auto',
                    max_length=32,
                )),
                ('comments', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('client', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='daily_readiness_checkins',
                    to='clients.client',
                )),
            ],
            options={
                'db_table': 'daily_readiness_checkins',
                'ordering': ['-date', '-created_at'],
            },
        ),
        migrations.AddField(
            model_name='dailytrainingrecommendation',
            name='modality',
            field=models.CharField(
                blank=True,
                choices=[
                    ('insanity', 'Insanity Video'),
                    ('hybrid', 'Hybrid'),
                    ('gym_strength', 'Gym Strength'),
                    ('mobility_recovery', 'Mobility Recovery'),
                    ('auto', 'Auto'),
                ],
                default='auto',
                help_text='Delivery modality: insanity, hybrid, gym_strength, mobility_recovery, auto.',
                max_length=32,
            ),
        ),
        migrations.AddField(
            model_name='dailytrainingrecommendation',
            name='intensity_level',
            field=models.PositiveSmallIntegerField(
                blank=True,
                help_text='Expected intensity level 1-10 from AI recommendation.',
                null=True,
                validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(10)],
            ),
        ),
        migrations.AddConstraint(
            model_name='dailyreadinesscheckin',
            constraint=models.UniqueConstraint(
                fields=('client', 'date'),
                name='daily_readiness_client_date_unique',
            ),
        ),
        migrations.AddIndex(
            model_name='dailyreadinesscheckin',
            index=models.Index(fields=['client', 'date'], name='daily_readi_client__idx'),
        ),
    ]
