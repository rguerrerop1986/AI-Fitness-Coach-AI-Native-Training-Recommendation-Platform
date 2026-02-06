# ClientProgressionState: closed-loop recommendation V1.1

from django.db import migrations, models
import django.db.models.deletion
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('tracking', '0007_daily_exercise_recommendation'),
        ('clients', '0004_client_height_m_and_level'),
    ]

    operations = [
        migrations.CreateModel(
            name='ClientProgressionState',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('current_load_score', models.FloatField(default=0.0)),
                ('intensity_bias', models.SmallIntegerField(
                    default=0,
                    help_text='Global intensity adjustment -2 to +2',
                    validators=[django.core.validators.MinValueValidator(-2), django.core.validators.MaxValueValidator(2)],
                )),
                ('preferred_types', models.JSONField(blank=True, default=dict, help_text='Type weights e.g. {"CARDIO": 0.2, "STRENGTH": 0.1}')),
                ('last_recommended_type', models.CharField(blank=True, max_length=20, null=True)),
                ('high_days_streak', models.PositiveSmallIntegerField(default=0, help_text='Consecutive days with HIGH intensity (for guardrail: max 2)')),
                ('cooldown_days_remaining', models.PositiveSmallIntegerField(default=0, help_text='Days to force low intensity after injury_risk (e.g. 3)')),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('client', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='progression_state',
                    to='clients.client',
                )),
            ],
            options={
                'db_table': 'client_progression_states',
            },
        ),
    ]
