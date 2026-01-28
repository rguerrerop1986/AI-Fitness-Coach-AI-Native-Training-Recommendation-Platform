"""
Management command to reset the database.

This command will:
1. Drop all tables (or flush the database)
2. Run all migrations
3. Optionally create demo data

Usage:
    python manage.py reset_database
    python manage.py reset_database --create-demo-data
    python manage.py reset_database --flush-only
"""

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connection
from django.conf import settings
import sys


class Command(BaseCommand):
    help = 'Reset the database by dropping all tables and running migrations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--no-input',
            action='store_true',
            help='Skip confirmation prompt',
        )
        parser.add_argument(
            '--create-demo-data',
            action='store_true',
            help='Create demo data after reset',
        )
        parser.add_argument(
            '--flush-only',
            action='store_true',
            help='Use flush instead of dropping tables (safer, keeps structure)',
        )

    def handle(self, *args, **options):
        no_input = options['no_input']
        create_demo_data = options['create_demo_data']
        flush_only = options['flush_only']

        # Warning message
        self.stdout.write(self.style.WARNING('=' * 70))
        self.stdout.write(self.style.WARNING('WARNING: This will DELETE ALL DATA in the database!'))
        self.stdout.write(self.style.WARNING('=' * 70))

        if not no_input:
            confirm = input('\nAre you sure you want to continue? (yes/no): ')
            if confirm.lower() not in ['yes', 'y']:
                self.stdout.write(self.style.ERROR('Operation cancelled.'))
                return

        try:
            if flush_only:
                # Use Django's flush command (safer, keeps table structure)
                self.stdout.write(self.style.SUCCESS('\nFlushing database...'))
                call_command('flush', verbosity=0, interactive=False)
                self.stdout.write(self.style.SUCCESS('✓ Database flushed successfully'))
            else:
                # Drop all tables and recreate
                self.stdout.write(self.style.SUCCESS('\nDropping all tables...'))
                with connection.cursor() as cursor:
                    # Get all table names
                    if 'postgresql' in settings.DATABASES['default']['ENGINE']:
                        # PostgreSQL
                        cursor.execute("""
                            SELECT tablename FROM pg_tables 
                            WHERE schemaname = 'public'
                        """)
                        tables = [row[0] for row in cursor.fetchall()]
                        
                        # Disable foreign key checks temporarily
                        cursor.execute('SET session_replication_role = replica;')
                        
                        # Drop all tables
                        for table in tables:
                            cursor.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE;')
                            self.stdout.write(f'  Dropped table: {table}')
                        
                        cursor.execute('SET session_replication_role = DEFAULT;')
                        
                    elif 'sqlite' in settings.DATABASES['default']['ENGINE']:
                        # SQLite
                        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                        tables = [row[0] for row in cursor.fetchall()]
                        
                        for table in tables:
                            if table != 'sqlite_sequence':
                                cursor.execute(f'DROP TABLE IF EXISTS "{table}";')
                                self.stdout.write(f'  Dropped table: {table}')
                    else:
                        # MySQL or other
                        cursor.execute("SHOW TABLES;")
                        tables = [row[0] for row in cursor.fetchall()]
                        
                        cursor.execute('SET FOREIGN_KEY_CHECKS = 0;')
                        for table in tables:
                            cursor.execute(f'DROP TABLE IF EXISTS `{table}`;')
                            self.stdout.write(f'  Dropped table: {table}')
                        cursor.execute('SET FOREIGN_KEY_CHECKS = 1;')

                self.stdout.write(self.style.SUCCESS('✓ All tables dropped'))

            # Run migrations
            self.stdout.write(self.style.SUCCESS('\nRunning migrations...'))
            call_command('migrate', verbosity=1)
            self.stdout.write(self.style.SUCCESS('✓ Migrations completed'))

            # Create demo data if requested
            if create_demo_data:
                self.stdout.write(self.style.SUCCESS('\nCreating demo data...'))
                try:
                    call_command('create_demo_users', verbosity=1)
                    self.stdout.write(self.style.SUCCESS('✓ Demo users created'))
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'  Could not create demo users: {e}'))

            self.stdout.write(self.style.SUCCESS('\n' + '=' * 70))
            self.stdout.write(self.style.SUCCESS('Database reset completed successfully!'))
            self.stdout.write(self.style.SUCCESS('=' * 70))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\nError resetting database: {e}'))
            import traceback
            self.stdout.write(self.style.ERROR(traceback.format_exc()))
            sys.exit(1)
