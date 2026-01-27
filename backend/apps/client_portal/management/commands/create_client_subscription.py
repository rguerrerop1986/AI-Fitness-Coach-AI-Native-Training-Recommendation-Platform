from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.hashers import make_password
from datetime import date, timedelta
from apps.clients.models import Client
from apps.client_portal.models import ClientSubscription


class Command(BaseCommand):
    help = 'Create a client subscription for accessing the portal'

    def add_arguments(self, parser):
        parser.add_argument('client_id', type=int, help='Client ID to create subscription for')
        parser.add_argument('username', type=str, help='Username for the client')
        parser.add_argument('password', type=str, help='Password for the client')
        parser.add_argument(
            '--duration',
            type=int,
            default=30,
            help='Subscription duration in days (default: 30)'
        )

    def handle(self, *args, **options):
        client_id = options['client_id']
        username = options['username']
        password = options['password']
        duration = options['duration']

        try:
            client = Client.objects.get(id=client_id)
        except Client.DoesNotExist:
            raise CommandError(f'Client with ID {client_id} does not exist')

        # Check if subscription already exists
        if ClientSubscription.objects.filter(client=client).exists():
            self.stdout.write(
                self.style.WARNING(f'Client {client.full_name} already has a subscription')
            )
            return

        # Check if username is already taken
        if ClientSubscription.objects.filter(username=username).exists():
            raise CommandError(f'Username "{username}" is already taken')

        # Create subscription
        subscription = ClientSubscription.objects.create(
            client=client,
            username=username,
            password_hash=make_password(password),
            status='active',
            subscription_start=date.today(),
            subscription_end=date.today() + timedelta(days=duration)
        )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created subscription for {client.full_name}:\n'
                f'  Username: {username}\n'
                f'  Duration: {duration} days\n'
                f'  Expires: {subscription.subscription_end}'
            )
        )
