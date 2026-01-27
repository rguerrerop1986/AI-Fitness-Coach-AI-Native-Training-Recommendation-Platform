#!/usr/bin/env python
"""
Script to create an admin account for the Fitness Coach App.
Run this script to create a superuser account.
"""

import os
import sys
import django

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fitness_coach.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

def create_admin_user():
    """Create an admin user with proper password hashing."""
    
    # Check if admin user already exists
    if User.objects.filter(username='admin').exists():
        print("Admin user already exists!")
        admin = User.objects.get(username='admin')
        admin.set_password('admin123')
        admin.save()
        print("Admin password updated!")
    else:
        # Create new admin user
        admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='admin123',
            first_name='Admin',
            last_name='User',
            role='coach',
            is_staff=True,
            is_superuser=True
        )
        print("Admin user created successfully!")
    
    print("\nAdmin credentials:")
    print("Username: admin")
    print("Password: admin123")
    print("\nYou can now log in to the application!")

def create_demo_users():
    """Create demo users with proper password hashing."""
    
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
        print("Coach user created successfully!")
    else:
        coach.set_password('demo123')
        coach.save()
        print("Coach password updated!")

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
        print("Assistant user created successfully!")
    else:
        assistant.set_password('demo123')
        assistant.save()
        print("Assistant password updated!")

    print("\nDemo credentials:")
    print("Coach: coach / demo123")
    print("Assistant: assistant / demo123")

if __name__ == '__main__':
    print("Creating admin and demo users...")
    create_admin_user()
    create_demo_users()
    print("\nAll users created successfully!")
