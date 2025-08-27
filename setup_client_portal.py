#!/usr/bin/env python3
"""
Setup script for the client portal feature.
This script creates demo client subscriptions and assigns plans.
"""

import os
import sys
import django
from datetime import date, timedelta

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fitness_coach.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from apps.clients.models import Client, Measurement
from apps.plans.models import DietPlan, WorkoutPlan, PlanAssignment
from apps.client_portal.models import ClientSubscription

User = get_user_model()


def create_demo_data():
    """Create demo data for the client portal."""
    
    print("🚀 Setting up Client Portal Demo Data...")
    
    # Get or create a coach user
    coach, created = User.objects.get_or_create(
        username='coach',
        defaults={
            'email': 'coach@example.com',
            'first_name': 'John',
            'last_name': 'Coach',
            'role': 'coach',
            'is_staff': True,
            'is_superuser': True,
        }
    )
    
    if created:
        coach.set_password('demo123')
        coach.save()
        print("✅ Created coach user")
    else:
        print("✅ Coach user already exists")
    
    # Get or create demo clients
    client1, created = Client.objects.get_or_create(
        email='john.doe@example.com',
        defaults={
            'first_name': 'John',
            'last_name': 'Doe',
            'date_of_birth': date(1990, 5, 15),
            'sex': 'M',
            'phone': '+1234567890',
            'height_cm': 175.0,
            'initial_weight_kg': 80.0,
            'notes': 'Demo client for testing',
            'consent_checkbox': True,
            'emergency_contact': 'Jane Doe - +1234567891',
        }
    )
    
    if created:
        print("✅ Created client: John Doe")
    else:
        print("✅ Client John Doe already exists")
    
    client2, created = Client.objects.get_or_create(
        email='jane.smith@example.com',
        defaults={
            'first_name': 'Jane',
            'last_name': 'Smith',
            'date_of_birth': date(1988, 8, 22),
            'sex': 'F',
            'phone': '+1234567892',
            'height_cm': 165.0,
            'initial_weight_kg': 65.0,
            'notes': 'Demo client for testing',
            'consent_checkbox': True,
            'emergency_contact': 'John Smith - +1234567893',
        }
    )
    
    if created:
        print("✅ Created client: Jane Smith")
    else:
        print("✅ Client Jane Smith already exists")
    
    # Create measurements for clients
    for client in [client1, client2]:
        measurement, created = Measurement.objects.get_or_create(
            client=client,
            date=date.today(),
            defaults={
                'weight_kg': client.initial_weight_kg,
                'body_fat_pct': 20.0,
                'chest_cm': 95.0 if client.sex == 'M' else 85.0,
                'waist_cm': 80.0 if client.sex == 'M' else 70.0,
                'hips_cm': 95.0 if client.sex == 'M' else 90.0,
                'bicep_cm': 35.0 if client.sex == 'M' else 28.0,
                'thigh_cm': 55.0 if client.sex == 'M' else 50.0,
                'calf_cm': 35.0 if client.sex == 'M' else 32.0,
            }
        )
        
        if created:
            print(f"✅ Created measurements for {client.full_name}")
    
    # Create demo diet plans
    diet_plan1, created = DietPlan.objects.get_or_create(
        title='Weight Loss Plan',
        defaults={
            'description': 'A balanced diet plan for weight loss',
            'goal': 'cut',
            'daily_calories': 1800,
            'protein_pct': 30.0,
            'carbs_pct': 40.0,
            'fat_pct': 30.0,
            'created_by': coach,
        }
    )
    
    if created:
        print("✅ Created diet plan: Weight Loss Plan")
    else:
        print("✅ Diet plan already exists")
    
    diet_plan2, created = DietPlan.objects.get_or_create(
        title='Muscle Building Plan',
        defaults={
            'description': 'High protein diet for muscle building',
            'goal': 'bulk',
            'daily_calories': 2500,
            'protein_pct': 35.0,
            'carbs_pct': 45.0,
            'fat_pct': 20.0,
            'created_by': coach,
        }
    )
    
    if created:
        print("✅ Created diet plan: Muscle Building Plan")
    else:
        print("✅ Diet plan already exists")
    
    # Create demo workout plans
    workout_plan1, created = WorkoutPlan.objects.get_or_create(
        title='Strength Training',
        defaults={
            'description': 'Progressive strength training program',
            'goal': 'strength',
            'created_by': coach,
        }
    )
    
    if created:
        print("✅ Created workout plan: Strength Training")
    else:
        print("✅ Workout plan already exists")
    
    workout_plan2, created = WorkoutPlan.objects.get_or_create(
        title='Cardio Fitness',
        defaults={
            'description': 'Cardiovascular fitness program',
            'goal': 'endurance',
            'created_by': coach,
        }
    )
    
    if created:
        print("✅ Created workout plan: Cardio Fitness")
    else:
        print("✅ Workout plan already exists")
    
    # Assign plans to clients
    assignments = [
        (client1, 'diet', diet_plan1, None),
        (client1, 'workout', None, workout_plan1),
        (client2, 'diet', diet_plan2, None),
        (client2, 'workout', None, workout_plan2),
    ]
    
    for client, plan_type, diet_plan, workout_plan in assignments:
        assignment, created = PlanAssignment.objects.get_or_create(
            client=client,
            plan_type=plan_type,
            defaults={
                'diet_plan': diet_plan,
                'workout_plan': workout_plan,
                'start_date': date.today(),
                'is_active': True,
                'assigned_by': coach,
            }
        )
        
        if created:
            plan_name = diet_plan.title if diet_plan else workout_plan.title
            print(f"✅ Assigned {plan_type} plan '{plan_name}' to {client.full_name}")
    
    # Create client subscriptions
    subscriptions = [
        (client1, 'john_doe', 'client123'),
        (client2, 'jane_smith', 'client456'),
    ]
    
    for client, username, password in subscriptions:
        subscription, created = ClientSubscription.objects.get_or_create(
            client=client,
            defaults={
                'username': username,
                'password_hash': make_password(password),
                'status': 'active',
                'subscription_start': date.today(),
                'subscription_end': date.today() + timedelta(days=90),
            }
        )
        
        if created:
            print(f"✅ Created subscription for {client.full_name}")
            print(f"   Username: {username}")
            print(f"   Password: {password}")
        else:
            print(f"✅ Subscription for {client.full_name} already exists")
    
    print("\n🎉 Client Portal setup complete!")
    print("\n📋 Demo Client Credentials:")
    print("   John Doe - Username: john_doe, Password: client123")
    print("   Jane Smith - Username: jane_smith, Password: client456")
    print("\n🔗 Access URLs:")
    print("   Coach Portal: http://localhost:5173")
    print("   Client Portal: http://localhost:5173/client/login")


if __name__ == '__main__':
    create_demo_data()
