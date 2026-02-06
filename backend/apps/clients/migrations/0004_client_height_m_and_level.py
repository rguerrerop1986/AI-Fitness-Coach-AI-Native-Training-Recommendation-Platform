# Migration: 1) Add height_m (meters), migrate from height_cm, remove height_cm. 2) Add client level.

from decimal import Decimal
from django.db import migrations, models


def height_cm_to_height_m(apps, schema_editor):
    """Convert height_cm to height_m. Values > 10 treated as cm (divide by 100)."""
    Client = apps.get_model('clients', 'Client')
    for c in Client.objects.all():
        if c.height_cm is None:
            c.height_m = Decimal('1.70')
        else:
            val = float(c.height_cm)
            if val > 10:
                c.height_m = round(Decimal(val) / 100, 2)
            elif Decimal('0.5') <= Decimal(str(val)) <= Decimal('2.5'):
                c.height_m = round(Decimal(str(val)), 2)
            else:
                c.height_m = round(Decimal(val) / 100, 2)
        c.save(update_fields=['height_m'])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0003_add_client_deactivation_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='client',
            name='height_m',
            field=models.DecimalField(
                decimal_places=2,
                max_digits=4,
                null=True,
                blank=True,
            ),
        ),
        migrations.RunPython(height_cm_to_height_m, noop),
        migrations.RemoveField(
            model_name='client',
            name='height_cm',
        ),
        migrations.AlterField(
            model_name='client',
            name='height_m',
            field=models.DecimalField(
                decimal_places=2,
                max_digits=4,
                default=Decimal('1.70'),
            ),
        ),
        migrations.AddField(
            model_name='client',
            name='level',
            field=models.CharField(
                choices=[
                    ('beginner', 'Principiante'),
                    ('intermediate', 'Intermedio'),
                    ('advanced', 'Avanzado'),
                ],
                default='beginner',
                max_length=12,
            ),
        ),
    ]
