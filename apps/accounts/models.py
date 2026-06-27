from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user with a restaurant-specific role."""

    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        MANAGER = "MANAGER", "Manager"
        WAITER = "WAITER", "Waiter"

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.WAITER,
    )
    phone = models.CharField(max_length=20, blank=True)

    @property
    def is_admin(self) -> bool:
        return self.role == self.Role.ADMIN or self.is_superuser

    @property
    def is_manager(self) -> bool:
        return self.role == self.Role.MANAGER

    @property
    def is_waiter(self) -> bool:
        return self.role == self.Role.WAITER

    def __str__(self) -> str:
        return f"{self.username} ({self.get_role_display()})"
