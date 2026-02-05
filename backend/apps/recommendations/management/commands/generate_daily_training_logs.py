"""
Management command: generate or refresh daily training suggestions for all clients
with an ACTIVE PlanCycle covering today (timezone-aware).
Idempotent: creates TrainingLog if missing; only fills suggestion when empty or NOT_DONE
without executed_exercise (so we can re-suggest after skip/not_done).
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction

from apps.clients.models import Client
from apps.plans.models import PlanCycle
from apps.tracking.models import TrainingLog
from apps.recommendations.services.training_recommender import suggest_exercise_for_today

VERSION = 'rules_v1'


class Command(BaseCommand):
    help = (
        'For each client with an ACTIVE PlanCycle covering today: get_or_create TrainingLog, '
        'then set suggested_exercise + recommendation_* when log has no suggestion or is NOT_DONE without executed_exercise.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            default=None,
            help='Date YYYY-MM-DD (default: today in server timezone)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Only print what would be done, do not save.',
        )

    def handle(self, *args, **options):
        date_str = options.get('date')
        dry_run = options.get('dry_run', False)

        if date_str:
            try:
                target_date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                self.stderr.write(self.style.ERROR(f'Invalid --date: {date_str}. Use YYYY-MM-DD.'))
                return
        else:
            target_date = timezone.localdate()

        self.stdout.write(f'Target date: {target_date} (dry_run={dry_run})')

        # Clients with ACTIVE plan covering target_date
        active_cycles = PlanCycle.objects.filter(
            status=PlanCycle.Status.ACTIVE,
            start_date__lte=target_date,
            end_date__gte=target_date,
        ).select_related('client')

        client_ids = list(active_cycles.values_list('client_id', flat=True).distinct())
        clients = list(Client.objects.filter(id__in=client_ids))

        updated = 0
        created = 0
        skipped = 0

        for client in clients:
            cycle = next((c for c in active_cycles if c.client_id == client.id), None)
            if not cycle:
                continue

            with transaction.atomic():
                log, was_created = TrainingLog.objects.get_or_create(
                    client=client,
                    date=target_date,
                    defaults={
                        'plan_cycle_id': cycle.id,
                        'coach_id': cycle.coach_id,
                        'execution_status': TrainingLog.ExecutionStatus.NOT_DONE,
                    },
                )
                if was_created:
                    created += 1
                    if not dry_run and log.plan_cycle_id is None:
                        log.plan_cycle_id = cycle.id
                        log.coach_id = cycle.coach_id
                        log.save(update_fields=['plan_cycle_id', 'coach_id'])

            # Suggest when: no suggested_exercise, or (NOT_DONE and no executed_exercise)
            needs_suggestion = (
                not log.suggested_exercise_id
                or (
                    log.execution_status == TrainingLog.ExecutionStatus.NOT_DONE
                    and not log.executed_exercise_id
                )
            )
            if not needs_suggestion:
                skipped += 1
                continue

            result = suggest_exercise_for_today(client, target_date)
            exercise = result.get('exercise')
            rationale = result.get('rationale', '')
            meta = result.get('meta') or {}
            confidence = result.get('confidence')

            if dry_run:
                self.stdout.write(
                    f'  [DRY-RUN] client={client.id} {client.full_name}: '
                    f'exercise={exercise.id if exercise else None} rationale={rationale[:50]}...'
                )
                updated += 1
                continue

            log.suggested_exercise = exercise
            log.recommendation_version = VERSION
            log.recommendation_meta = meta
            log.recommendation_confidence = confidence
            # Append rationale to notes (do not overwrite user notes)
            if rationale:
                existing = (log.notes or '').strip()
                if existing and rationale not in existing:
                    log.notes = f"{existing}\n[Rutina] {rationale}"
                elif not existing:
                    log.notes = f"[Rutina] {rationale}"
            log.save(update_fields=[
                'suggested_exercise_id', 'recommendation_version', 'recommendation_meta',
                'recommendation_confidence', 'notes', 'updated_at',
            ])
            updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Done: created={created}, updated={updated}, skipped={skipped}'
            )
        )
