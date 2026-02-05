# Add BMI (IMC) to CheckIn - calculated from weight_kg and height_m

from django.db import migrations, models


def backfill_bmi(apps, schema_editor):
    """Fill bmi for existing check-ins that have weight_kg and height_m."""
    CheckIn = apps.get_model('tracking', 'CheckIn')
    for obj in CheckIn.objects.filter(weight_kg__isnull=False, height_m__isnull=False).exclude(height_m=0):
        try:
            h = float(obj.height_m)
            if h <= 0:
                continue
            w = float(obj.weight_kg)
            obj.bmi = round(w / (h * h), 2)
            obj.save(update_fields=['bmi'])
        except (TypeError, ValueError, ZeroDivisionError):
            pass


class Migration(migrations.Migration):

    dependencies = [
        ('tracking', '0005_add_structural_checkin_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='checkin',
            name='bmi',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text='Índice de Masa Corporal (calculado: weight_kg / height_m²)',
                max_digits=5,
                null=True,
            ),
        ),
        migrations.RunPython(backfill_bmi, migrations.RunPython.noop),
    ]
