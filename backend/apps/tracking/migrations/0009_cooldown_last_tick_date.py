# Cooldown by calendar day: last tick date for day-based decrement.
# PR note: cooldown ahora es por día calendario; tick en GET/generate (no por sesión completada).

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracking', '0008_client_progression_state'),
    ]

    operations = [
        migrations.AddField(
            model_name='clientprogressionstate',
            name='cooldown_last_tick_date',
            field=models.DateField(
                blank=True,
                help_text='Last calendar date when cooldown was ticked (for day-based decrement)',
                null=True,
            ),
        ),
    ]
