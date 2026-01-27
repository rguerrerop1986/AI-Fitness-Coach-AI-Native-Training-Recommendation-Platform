from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user model with role-based permissions."""
    
    class Role(models.TextChoices):
        COACH = 'coach', 'Coach'
        ASSISTANT = 'assistant', 'Assistant'
        CLIENT = 'client', 'Client'
    
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.COACH
    )
    phone = models.CharField(max_length=20, blank=True)
    
    class Meta:
        db_table = 'users'
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.role})"
    
    @property
    def is_coach(self):
        return self.role == self.Role.COACH
    
    @property
    def is_assistant(self):
        return self.role == self.Role.ASSISTANT
    
    @property
    def is_client(self):
        return self.role == self.Role.CLIENT
