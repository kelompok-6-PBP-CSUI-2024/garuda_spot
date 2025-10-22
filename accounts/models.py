# accounts/models.py (keep exactly this)
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    class Roles(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        USER  = "USER",  "User"

    role = models.CharField(max_length=10, choices=Roles.choices, default=Roles.USER)

    @property
    def is_admin(self) -> bool:
        return self.role == self.Roles.ADMIN
