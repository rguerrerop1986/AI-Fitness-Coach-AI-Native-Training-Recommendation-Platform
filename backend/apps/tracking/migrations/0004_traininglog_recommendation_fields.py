# Generated manually for Rutina Diaria Inteligente

from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('tracking', '0003_traininglog_dietlog'),
    ]

    operations = [
        migrations.AddField(
            model_name='traininglog',
            name='recommendation_version',
            field=models.CharField(blank=True, default='rules_v1', max_length=50),
        ),
        migrations.AddField(
            model_name='traininglog',
            name='recommendation_meta',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='traininglog',
            name='recommendation_confidence',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=3,
                null=True,
                validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(1)],
            ),
        ),
        migrations.AlterField(
            model_name='traininglog',
            name='execution_status',
            field=models.CharField(
                choices=[
                    ('not_done', 'Not Done'),
                    ('partial', 'Partial'),
                    ('done', 'Done'),
                    ('skipped', 'Skipped'),
                    ('replaced', 'Replaced'),
                    ('injury_stop', 'Injury Stop'),
                    ('sick', 'Sick'),
                ],
                default='not_done',
                max_length=20,
            ),
        ),
    ]
