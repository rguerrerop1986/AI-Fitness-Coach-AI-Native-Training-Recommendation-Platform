#!/usr/bin/env python
"""
Script to set up the database for the Fitness Coach App.
This script will:
1. Run Django migrations
2. Create admin and demo users
"""

import os
import sys
import django

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fitness_coach.settings')
django.setup()

from django.core.management import execute_from_command_line
from django.contrib.auth import get_user_model

User = get_user_model()

def run_migrations():
    """Run Django migrations."""
    print("Running migrations...")
    execute_from_command_line(['manage.py', 'migrate'])
    print("Migrations completed!")

def create_users():
    """Create admin and demo users."""
    print("Creating users...")
    
    # Create admin user
    admin, created = User.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@example.com',
            'first_name': 'Admin',
            'last_name': 'User',
            'role': 'coach',
            'is_staff': True,
            'is_superuser': True,
        }
    )
    
    if created:
        admin.set_password('admin123')
        admin.save()
        print("✅ Admin user created successfully!")
    else:
        admin.set_password('admin123')
        admin.save()
        print("✅ Admin password updated!")

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
        print("✅ Coach user created successfully!")
    else:
        coach.set_password('demo123')
        coach.save()
        print("✅ Coach password updated!")

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
        print("✅ Assistant user created successfully!")
    else:
        assistant.set_password('demo123')
        assistant.save()
        print("✅ Assistant password updated!")

    print("\n🎉 All users created successfully!")
    print("\n📋 Login Credentials:")
    print("   Admin: admin / admin123")
    print("   Coach: coach / demo123")
    print("   Assistant: assistant / demo123")

if __name__ == '__main__':
    print("🚀 Setting up Fitness Coach App database...")
    run_migrations()
    create_users()
    print("\n✅ Database setup completed!")
