from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Create demo users for the fitness coach app'

    def handle(self, *args, **options):
        # Create coach user
        coach, created = User.objects.get_or_create(
            username='coach',
            defaults={
                'email': 'coach@example.com',
                'first_name': 'John',
                'last_name': 'Coach',
                'role': 'coach',
                'phone': '+1234567890',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        
        if created:
            coach.set_password('demo123')
            coach.save()
            self.stdout.write(
                self.style.SUCCESS('Successfully created coach user')
            )
        else:
            coach.set_password('demo123')
            coach.save()
            self.stdout.write(
                self.style.SUCCESS('Updated coach user password')
            )

        # Create assistant user
        assistant, created = User.objects.get_or_create(
            username='assistant',
            defaults={
                'email': 'assistant@example.com',
                'first_name': 'Sarah',
                'last_name': 'Assistant',
                'role': 'assistant',
                'phone': '+1234567891',
            }
        )
        
        if created:
            assistant.set_password('demo123')
            assistant.save()
            self.stdout.write(
                self.style.SUCCESS('Successfully created assistant user')
            )
        else:
            assistant.set_password('demo123')
            assistant.save()
            self.stdout.write(
                self.style.SUCCESS('Updated assistant user password')
            )

        self.stdout.write(
            self.style.SUCCESS('Demo users created successfully!')
        )
        self.stdout.write('Coach: coach / demo123')
        self.stdout.write('Assistant: assistant / demo123')
