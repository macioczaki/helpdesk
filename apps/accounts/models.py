from django.contrib.auth.models import AbstractUser
from django.db import models


class Department(models.Model):
    name = models.CharField(max_length=128, unique=True)
    building = models.CharField(max_length=64, blank=True)
    floor = models.CharField(max_length=16, blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Dział"
        verbose_name_plural = "Działy"

    def __str__(self):
        return self.name


class User(AbstractUser):
    class Role(models.TextChoices):
        EMPLOYEE = "EMPLOYEE", "Pracownik"
        TECHNICIAN = "TECHNICIAN", "Technik"
        ADMIN = "ADMIN", "Administrator"

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.EMPLOYEE,
        verbose_name="Rola",
    )
    department = models.ForeignKey(
        Department,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="users",
        verbose_name="Dział",
    )
    phone = models.CharField(max_length=32, blank=True, verbose_name="Telefon")
    room = models.CharField(max_length=32, blank=True, verbose_name="Pokój")

    class Meta:
        verbose_name = "Użytkownik"
        verbose_name_plural = "Użytkownicy"

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    @property
    def is_technician(self):
        return self.role in {self.Role.TECHNICIAN, self.Role.ADMIN}

    @property
    def is_admin_role(self):
        return self.role == self.Role.ADMIN
