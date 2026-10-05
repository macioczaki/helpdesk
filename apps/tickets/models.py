import os
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


def attachment_upload_to(instance, filename):
    ext = os.path.splitext(filename)[1]
    return f"tickets/{instance.ticket_id}/{uuid.uuid4().hex}{ext}"


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
        choices=[
            ("LOW", "Niski"),
            ("NORMAL", "Normalny"),
            ("HIGH", "Wysoki"),
            ("CRITICAL", "Krytyczny"),
        ],
        default="NORMAL",
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Kategoria"
        verbose_name_plural = "Kategorie"

    def __str__(self):
        return f"{self.parent.name} / {self.name}" if self.parent else self.name


class SLA(models.Model):
    priority = models.CharField(
        max_length=16,
        choices=[
            ("LOW", "Niski"),
            ("NORMAL", "Normalny"),
            ("HIGH", "Wysoki"),
            ("CRITICAL", "Krytyczny"),
        ],
        unique=True,
    )
    response_minutes = models.PositiveIntegerField(
        help_text="Czas do pierwszej reakcji (w minutach)."
    )
    resolve_minutes = models.PositiveIntegerField(help_text="Czas do rozwiązania (w minutach).")

    class Meta:
        verbose_name = "SLA"
        verbose_name_plural = "SLA"

    def __str__(self):
        return f"{self.get_priority_display()} — reakcja {self.response_minutes} min, rozwiązanie {self.resolve_minutes} min"


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
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.NEW)
    priority = models.CharField(max_length=16, choices=Priority.choices, default=Priority.NORMAL)
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
    due_at = models.DateTimeField(null=True, blank=True)

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

    def calculate_due_at(self):
        try:
            sla = SLA.objects.get(priority=self.priority)
        except SLA.DoesNotExist:
            return None
        return self.created_at + timezone.timedelta(minutes=sla.resolve_minutes)

    @property
    def sla_breached(self):
        if not self.due_at or self.status in {self.Status.RESOLVED, self.Status.CLOSED}:
            return False
        return timezone.now() > self.due_at

    def mark_resolved(self):
        self.status = self.Status.RESOLVED
        self.resolved_at = timezone.now()
        self.save(update_fields=["status", "resolved_at", "updated_at"])

    def mark_closed(self):
        self.status = self.Status.CLOSED
        self.closed_at = timezone.now()
        self.save(update_fields=["status", "closed_at", "updated_at"])


class TicketComment(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="ticket_comments"
    )
    body = models.TextField()
    is_internal = models.BooleanField(
        default=False,
        help_text="Komentarz wewnętrzny — widoczny tylko dla techników i adminów.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "Komentarz"
        verbose_name_plural = "Komentarze"

    def __str__(self):
        return f"#{self.ticket.number} — {self.author} ({self.created_at:%Y-%m-%d %H:%M})"


class TicketAttachment(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="attachments")
    comment = models.ForeignKey(
        TicketComment,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="attachments",
    )
    file = models.FileField(upload_to=attachment_upload_to)
    original_name = models.CharField(max_length=255)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="ticket_attachments"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "Załącznik"
        verbose_name_plural = "Załączniki"

    def __str__(self):
        return self.original_name

    def save(self, *args, **kwargs):
        if not self.original_name and self.file:
            self.original_name = os.path.basename(self.file.name)
        super().save(*args, **kwargs)


class TicketHistory(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="history")
    field = models.CharField(max_length=64)
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="ticket_changes",
    )
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-changed_at"]
        verbose_name = "Historia zgłoszenia"
        verbose_name_plural = "Historia zgłoszeń"

    def __str__(self):
        return f"#{self.ticket.number} — {self.field}: {self.old_value!r} → {self.new_value!r}"
