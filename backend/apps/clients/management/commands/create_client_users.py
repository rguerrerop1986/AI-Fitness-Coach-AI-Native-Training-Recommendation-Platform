from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from apps.clients.models import Client
import secrets
import string

User = get_user_model()


class Command(BaseCommand):
    help = 'Create User accounts for Clients that do not have a linked user account'

    def add_arguments(self, parser):
        parser.add_argument(
            '--password',
            type=str,
            help='Set a specific password for all created users (otherwise generates random)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating users',
        )

    def generate_password(self, length=12):
        """Generate a random password."""
        alphabet = string.ascii_letters + string.digits + string.punctuation
        return ''.join(secrets.choice(alphabet) for _ in range(length))

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        password = options.get('password')
        
        clients_without_user = Client.objects.filter(user__isnull=True)
        
        if not clients_without_user.exists():
            self.stdout.write(self.style.SUCCESS('All clients already have user accounts.'))
            return
        
        self.stdout.write(f'Found {clients_without_user.count()} clients without user accounts.')
        
        created_count = 0
        skipped_count = 0
        
        with transaction.atomic():
            for client in clients_without_user:
                # Generate username from email or use email as username
                username = client.email.split('@')[0]
                
                # Ensure username is unique
                base_username = username
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}_{counter}"
                    counter += 1
                
                # Generate password if not provided
                if not password:
                    generated_password = self.generate_password()
                else:
                    generated_password = password
                
                if dry_run:
                    self.stdout.write(
                        f'Would create user: username={username}, email={client.email}, '
                        f'password={generated_password if password else "***random***"}'
                    )
                else:
                    try:
                        user = User.objects.create_user(
                            username=username,
                            email=client.email,
                            password=generated_password,
                            role=User.Role.CLIENT,
                            first_name=client.first_name,
                            last_name=client.last_name,
                        )
                        client.user = user
                        client.save()
                        
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'Created user for {client.full_name}: '
                                f'username={username}, password={generated_password}'
                            )
                        )
                        created_count += 1
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'Failed to create user for {client.full_name}: {e}')
                        )
                        skipped_count += 1
        
        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nSummary: Created {created_count} user(s), Skipped {skipped_count} client(s).'
                )
            )
            if created_count > 0:
                self.stdout.write(
                    self.style.WARNING(
                        '\nIMPORTANT: Please share the generated passwords with clients securely. '
                        'They should change their passwords after first login.'
                    )
                )
