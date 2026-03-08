"""
Load initial Insanity workout videos into TrainingVideo catalog.
Usage: python manage.py seed_insanity_videos
"""
from django.core.management.base import BaseCommand
from apps.training.models import TrainingVideo


INSANITY_VIDEOS = [
    {
        "name": "Cardio Recovery",
        "program": "Insanity",
        "category": TrainingVideo.Category.RECOVERY,
        "difficulty": TrainingVideo.Difficulty.LOW,
        "duration_minutes": 33,
        "description": "Low-impact recovery with stretching and light movement.",
        "stresses_legs": True,
        "stresses_upper_body": False,
        "stresses_core": True,
        "explosive": False,
    },
    {
        "name": "Core Cardio and Balance",
        "program": "Insanity",
        "category": TrainingVideo.Category.CORE,
        "difficulty": TrainingVideo.Difficulty.MEDIUM,
        "duration_minutes": 40,
        "description": "Core focus with cardio and balance work.",
        "stresses_legs": True,
        "stresses_upper_body": False,
        "stresses_core": True,
        "explosive": False,
    },
    {
        "name": "Plyometric Cardio Circuit",
        "program": "Insanity",
        "category": TrainingVideo.Category.PLYOMETRICS,
        "difficulty": TrainingVideo.Difficulty.HIGH,
        "duration_minutes": 41,
        "description": "High-intensity plyometric and cardio circuit.",
        "stresses_legs": True,
        "stresses_upper_body": True,
        "stresses_core": True,
        "explosive": True,
    },
    {
        "name": "Cardio Power and Resistance",
        "program": "Insanity",
        "category": TrainingVideo.Category.MIXED,
        "difficulty": TrainingVideo.Difficulty.MEDIUM,
        "duration_minutes": 40,
        "description": "Cardio with resistance/bodyweight moves.",
        "stresses_legs": True,
        "stresses_upper_body": True,
        "stresses_core": True,
        "explosive": False,
    },
    {
        "name": "Pure Cardio",
        "program": "Insanity",
        "category": TrainingVideo.Category.CARDIO,
        "difficulty": TrainingVideo.Difficulty.HIGH,
        "duration_minutes": 40,
        "description": "Non-stop cardio, no rest.",
        "stresses_legs": True,
        "stresses_upper_body": False,
        "stresses_core": True,
        "explosive": True,
    },
    {
        "name": "Max Interval Circuit",
        "program": "Insanity",
        "category": TrainingVideo.Category.MIXED,
        "difficulty": TrainingVideo.Difficulty.MAX,
        "duration_minutes": 60,
        "description": "Long intervals, max effort.",
        "stresses_legs": True,
        "stresses_upper_body": True,
        "stresses_core": True,
        "explosive": True,
    },
    {
        "name": "Max Interval Plyo",
        "program": "Insanity",
        "category": TrainingVideo.Category.PLYOMETRICS,
        "difficulty": TrainingVideo.Difficulty.MAX,
        "duration_minutes": 55,
        "description": "Plyometric intervals at max intensity.",
        "stresses_legs": True,
        "stresses_upper_body": False,
        "stresses_core": True,
        "explosive": True,
    },
    {
        "name": "Max Cardio Conditioning",
        "program": "Insanity",
        "category": TrainingVideo.Category.CARDIO,
        "difficulty": TrainingVideo.Difficulty.MAX,
        "duration_minutes": 45,
        "description": "Peak cardio conditioning session.",
        "stresses_legs": True,
        "stresses_upper_body": False,
        "stresses_core": True,
        "explosive": True,
    },
]


class Command(BaseCommand):
    help = "Seed TrainingVideo catalog with Insanity workouts."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete existing Insanity videos before seeding (by program=Insanity).",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            deleted, _ = TrainingVideo.objects.filter(program="Insanity").delete()
            self.stdout.write(self.style.WARNING(f"Deleted {deleted} existing Insanity video(s)."))
        created = 0
        for data in INSANITY_VIDEOS:
            _, was_created = TrainingVideo.objects.get_or_create(
                name=data["name"],
                program=data["program"],
                defaults=data,
            )
            if was_created:
                created += 1
        self.stdout.write(self.style.SUCCESS(f"Seeded {created} new Insanity video(s)."))
