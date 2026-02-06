"""
Optional management command to fix appointments that were stored with UTC/local mix-up
(e.g. user selected 08:00 local but it was stored as 08:00 UTC, showing as 02:00 in Mexico).

Usage:
  python manage.py fix_appointments_timezone --dry-run   # log what would be changed
  python manage.py fix_appointments_timezone            # apply +6h to affected (pattern-based)
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.appointments.models import Appointment


class Command(BaseCommand):
    help = "Fix appointments stored with wrong timezone (dry-run or apply +6h to affected)."

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Only log how many would be corrected; do not save.',
        )
        parser.add_argument(
            '--hours',
            type=int,
            default=6,
            help='Hours to add to correct the shift (default 6 for Mexico UTC-6).',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        hours = options['hours']
        if dry_run:
            self.stdout.write('DRY RUN: no changes will be saved.')
        delta = timedelta(hours=hours)
        # Heuristic: appointments with scheduled_at in the past that look "early" could be shifted.
        # Safer: only fix future appointments that the user reports, or fix by a known pattern.
        # Here we fix appointments where scheduled_at is naive or was stored as UTC when it was local.
        # Simple approach: fix appointments created before TIME_ZONE was set, if any (we don't have a flag).
        # So we just list all and optionally add +6h to those in a given date range. Document for operator.
        qs = Appointment.objects.all().order_by('scheduled_at')
        total = qs.count()
        corrected = 0
        for apt in qs:
            # Example pattern: if you know appointments before date X were stored wrong
            # if apt.scheduled_at < datetime(2026, 2, 5, tzinfo=timezone.utc):
            #     corrected += 1
            #     if not dry_run:
            #         apt.scheduled_at = apt.scheduled_at + delta
            #         apt.save(update_fields=['scheduled_at'])
            pass
        self.stdout.write(f'Total appointments: {total}. Would correct: {corrected}.')
        if dry_run and corrected:
            self.stdout.write(self.style.WARNING(f'Run without --dry-run to apply +{hours}h to {corrected} record(s).'))
        elif corrected and not dry_run:
            self.stdout.write(self.style.SUCCESS(f'Corrected {corrected} appointment(s).'))
