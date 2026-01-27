from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction, models
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
            dest='default_password',
            help='Set a specific password for all created users (otherwise generates random)',
        )
        parser.add_argument(
            '--default-password',
            type=str,
            help='Alias for --password (for local/dev use)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating users',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Recreate users for clients that have invalid/missing user links',
        )

    def generate_password(self, length=12):
        """Generate a random password."""
        alphabet = string.ascii_letters + string.digits + string.punctuation
        return ''.join(secrets.choice(alphabet) for _ in range(length))

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options.get('force', False)
        password = options.get('default_password') or options.get('password')
        
        # Find clients without user or with invalid user links
        if force:
            # Find clients where user is None, or user exists but role is not 'client', or user doesn't exist
            clients_needing_user = Client.objects.filter(
                models.Q(user__isnull=True) |
                ~models.Q(user__role='client')
            )
        else:
            clients_needing_user = Client.objects.filter(user__isnull=True)
        
        if not clients_needing_user.exists():
            self.stdout.write(self.style.SUCCESS('All clients already have valid user accounts.'))
            return
        
        self.stdout.write(f'Found {clients_needing_user.count()} clients needing user accounts.')
        
        created_count = 0
        skipped_count = 0
        errors = []
        
        with transaction.atomic():
            for client in clients_needing_user:
                # If force mode and user exists but is invalid, unlink it
                if force and client.user:
                    if client.user.role != User.Role.CLIENT:
                        self.stdout.write(
                            self.style.WARNING(
                                f'Unlinking invalid user (role={client.user.role}) for {client.full_name}'
                            )
                        )
                        client.user = None
                        client.save()
                
                # Generate username strategy: prefer email prefix, fallback to client_<id>
                if client.email:
                    username = client.email.split('@')[0]
                    # Clean username (remove dots, special chars)
                    username = username.replace('.', '_').replace('-', '_').lower()
                else:
                    username = f"client_{client.id}"
                
                # Ensure username is unique and valid (Django username requirements)
                base_username = username[:150]  # Django username max length
                counter = 1
                while User.objects.filter(username=base_username).exists():
                    base_username = f"{username[:140]}_{counter}"
                    counter += 1
                    if counter > 1000:  # Safety limit
                        base_username = f"client_{client.id}_{secrets.token_hex(4)}"
                        break
                
                username = base_username
                
                # Generate password if not provided
                if not password:
                    generated_password = self.generate_password()
                else:
                    generated_password = password
                
                if dry_run:
                    self.stdout.write(
                        f'Would create user: username={username}, email={client.email or "N/A"}, '
                        f'password={generated_password if password else "***random***"}'
                    )
                else:
                    try:
                        user = User.objects.create_user(
                            username=username,
                            email=client.email or '',
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
                        error_msg = f'Failed to create user for {client.full_name}: {e}'
                        errors.append(error_msg)
                        self.stdout.write(self.style.ERROR(error_msg))
                        skipped_count += 1
        
        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nSummary: Created {created_count} user(s), Skipped {skipped_count} client(s).'
                )
            )
            if errors:
                self.stdout.write(self.style.ERROR(f'\nErrors encountered: {len(errors)}'))
                for error in errors[:5]:  # Show first 5 errors
                    self.stdout.write(f'  - {error}')
                if len(errors) > 5:
                    self.stdout.write(f'  ... and {len(errors) - 5} more errors')
            if created_count > 0:
                self.stdout.write(
                    self.style.WARNING(
                        '\nIMPORTANT: Please share the generated passwords with clients securely. '
                        'They should change their passwords after first login.'
                    )
                )
