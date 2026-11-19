from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = (
        ("patient", "Patient"),
        ("admin", "Admin"),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="patient")
    phone = models.CharField(max_length=30, blank=True)

    def __str__(self):
        return self.username
