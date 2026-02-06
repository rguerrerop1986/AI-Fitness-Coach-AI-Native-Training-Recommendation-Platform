# Migration: Add Client.coach FK and backfill clients + training_logs/diet_logs coach_id

from django.conf import settings
from django.db import migrations, models


def backfill_coach_ids(apps, schema_editor):
    """Backfill clients.coach_id = first coach (id=1); then training_logs and diet_logs from client.coach_id."""
    User = apps.get_model(settings.AUTH_USER_MODEL)
    Client = apps.get_model('clients', 'Client')
    TrainingLog = apps.get_model('tracking', 'TrainingLog')
    DietLog = apps.get_model('tracking', 'DietLog')

    first_coach = User.objects.filter(role='coach').order_by('id').first()
    if not first_coach:
        return

    # Backfill clients: set coach_id = first coach where null
    Client.objects.filter(coach_id__isnull=True).update(coach_id=first_coach.id)

    # Backfill training_logs: set coach_id from client where log.coach_id is null
    for log in TrainingLog.objects.filter(coach_id__isnull=True).select_related('client'):
        if log.client_id and log.client.coach_id:
            log.coach_id = log.client.coach_id
            log.save(update_fields=['coach_id'])

    # Backfill diet_logs: same
    for log in DietLog.objects.filter(coach_id__isnull=True).select_related('client'):
        if log.client_id and log.client.coach_id:
            log.coach_id = log.client.coach_id
            log.save(update_fields=['coach_id'])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('clients', '0004_client_height_m_and_level'),
        ('tracking', '0003_traininglog_dietlog'),
    ]

    operations = [
        migrations.AddField(
            model_name='client',
            name='coach',
            field=models.ForeignKey(
                blank=True,
                help_text='Coach responsible for this client (must have role=coach)',
                null=True,
                on_delete=models.PROTECT,
                related_name='clients',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.RunPython(backfill_coach_ids, noop),
    ]
