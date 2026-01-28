from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string


User = get_user_model()


class Command(BaseCommand):
    help = "Create/update Sandy as administrator (superuser)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--password",
            type=str,
            default=None,
            help="Password for the user. If omitted, a random password is generated and printed.",
        )
        parser.add_argument(
            "--email",
            type=str,
            default="sandy@example.com",
            help="Email for Sandy (default: sandy@example.com).",
        )

    def handle(self, *args, **options):
        username = "sandy"
        email = options["email"]
        password = options["password"] or get_random_string(14)

        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "email": email,
                "first_name": "Sandy",
                "last_name": "Admin",
                "role": "coach",
                "is_staff": True,
                "is_superuser": True,
            },
        )

        # Ensure admin flags/role are correct even if user existed
        user.email = email
        user.first_name = user.first_name or "Sandy"
        user.last_name = user.last_name or "Admin"
        user.role = "coach"
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save()

        action = "Created" if created else "Updated"
        self.stdout.write(self.style.SUCCESS(f"{action} admin user '{username}'"))
        self.stdout.write(f"Username: {username}")
        self.stdout.write(f"Email: {user.email}")
        self.stdout.write(f"Password: {password}")
