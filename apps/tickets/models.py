from django.conf import settings
from django.db import models
from django.utils import timezone


class Category(models.Model):
    name = models.CharField(max_length=128, unique=True)
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="children",
    )
    default_priority = models.CharField(
        max_length=16,
        choices=[("LOW", "Niski"), ("NORMAL", "Normalny"), ("HIGH", "Wysoki"), ("CRITICAL", "Krytyczny")],
        default="NORMAL",
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Kategoria"
        verbose_name_plural = "Kategorie"

    def __str__(self):
        return f"{self.parent.name} / {self.name}" if self.parent else self.name


class Ticket(models.Model):
    class Status(models.TextChoices):
        NEW = "NEW", "Nowe"
        IN_PROGRESS = "IN_PROGRESS", "W realizacji"
        WAITING = "WAITING", "Oczekuje"
        RESOLVED = "RESOLVED", "Rozwiązane"
        CLOSED = "CLOSED", "Zamknięte"

    class Priority(models.TextChoices):
        LOW = "LOW", "Niski"
        NORMAL = "NORMAL", "Normalny"
        HIGH = "HIGH", "Wysoki"
        CRITICAL = "CRITICAL", "Krytyczny"

    number = models.CharField(max_length=32, unique=True, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.NEW
    )
    priority = models.CharField(
        max_length=16, choices=Priority.choices, default=Priority.NORMAL
    )
    category = models.ForeignKey(
        Category,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="tickets",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="tickets_created",
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="tickets_assigned",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Zgłoszenie"
        verbose_name_plural = "Zgłoszenia"
        indexes = [
            models.Index(fields=["status", "assigned_to"]),
            models.Index(fields=["created_by", "-created_at"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self):
        return f"{self.number} — {self.title}"

    def save(self, *args, **kwargs):
        if not self.number:
            self.number = self._generate_number()
        super().save(*args, **kwargs)

    @staticmethod
    def _generate_number():
        year = timezone.now().year
        prefix = f"TICK-{year}-"
        last = (
            Ticket.objects.filter(number__startswith=prefix)
            .order_by("-number")
            .values_list("number", flat=True)
            .first()
        )
        if last:
            seq = int(last.rsplit("-", 1)[1]) + 1
        else:
            seq = 1
        return f"{prefix}{seq:04d}"

    def mark_resolved(self):
        self.status = self.Status.RESOLVED
        self.resolved_at = timezone.now()
        self.save(update_fields=["status", "resolved_at", "updated_at"])

    def mark_closed(self):
        self.status = self.Status.CLOSED
        self.closed_at = timezone.now()
        self.save(update_fields=["status", "closed_at", "updated_at"])