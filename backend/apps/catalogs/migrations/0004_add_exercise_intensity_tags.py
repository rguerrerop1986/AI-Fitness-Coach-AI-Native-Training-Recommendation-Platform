# Generated manually for Rutina Diaria Inteligente

from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('catalogs', '0003_add_exercise_fields_and_training_entry'),
    ]

    operations = [
        migrations.AddField(
            model_name='exercise',
            name='intensity',
            field=models.PositiveSmallIntegerField(
                default=5,
                help_text='Intensity level 1-10 for recommendation engine',
                validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(10)],
            ),
        ),
        migrations.AddField(
            model_name='exercise',
            name='tags',
            field=models.JSONField(
                blank=True,
                default=list,
                help_text='Tags for filtering: e.g. ["hiit", "mobility", "low_impact"]',
            ),
        ),
    ]
