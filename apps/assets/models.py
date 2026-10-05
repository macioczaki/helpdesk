from django.conf import settings
from django.db import models
from django.utils import timezone


class AssetCategory(models.Model):
    name = models.CharField(max_length=128, unique=True)
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="children",
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Kategoria majątku"
        verbose_name_plural = "Kategorie majątku"

    def __str__(self):
        return f"{self.parent.name} / {self.name}" if self.parent else self.name


class Location(models.Model):
    building = models.CharField(max_length=64)
    floor = models.CharField(max_length=16, blank=True)
    room = models.CharField(max_length=32, blank=True)

    class Meta:
        ordering = ["building", "floor", "room"]
        verbose_name = "Lokalizacja"
        verbose_name_plural = "Lokalizacje"
        unique_together = [("building", "floor", "room")]

    def __str__(self):
        parts = [self.building, self.floor, self.room]
        return " / ".join(p for p in parts if p)


class Asset(models.Model):
    class Status(models.TextChoices):
        IN_USE = "IN_USE", "W użyciu"
        IN_STOCK = "IN_STOCK", "W magazynie"
        REPAIR = "REPAIR", "W naprawie"
        RETIRED = "RETIRED", "Wycofany"

    class Type(models.TextChoices):
        COMPUTER = "COMPUTER", "Komputer"
        LAPTOP = "LAPTOP", "Laptop"
        MONITOR = "MONITOR", "Monitor"
        PRINTER = "PRINTER", "Drukarka"
        PHONE = "PHONE", "Telefon"
        NETWORK = "NETWORK", "Urządzenie sieciowe"
        OTHER = "OTHER", "Inne"

    tag = models.CharField(
        max_length=64,
        unique=True,
        help_text="Unikalny tag QR/kod inwentarzowy. Zostanie wygenerowany, jeśli pusty.",
    )
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=16, choices=Type.choices, default=Type.OTHER)
    category = models.ForeignKey(
        AssetCategory,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assets",
    )
    manufacturer = models.CharField(max_length=128, blank=True)
    model_name = models.CharField(max_length=128, blank=True, verbose_name="Model")
    serial_number = models.CharField(max_length=128, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.IN_STOCK)
    location = models.ForeignKey(
        Location,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assets",
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assets_assigned",
    )
    purchase_date = models.DateField(null=True, blank=True)
    warranty_until = models.DateField(null=True, blank=True)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["tag"]
        verbose_name = "Zasób"
        verbose_name_plural = "Zasoby"
        indexes = [
            models.Index(fields=["status", "type"]),
            models.Index(fields=["assigned_to"]),
            models.Index(fields=["location"]),
        ]

    def __str__(self):
        return f"{self.tag} — {self.name}"

    def save(self, *args, **kwargs):
        if not self.tag:
            self.tag = self._generate_tag()
        super().save(*args, **kwargs)

    @staticmethod
    def _generate_tag():
        year = timezone.now().year
        prefix = f"AST-{year}-"
        last = (
            Asset.objects.filter(tag__startswith=prefix)
            .order_by("-tag")
            .values_list("tag", flat=True)
            .first()
        )
        if last:
            seq = int(last.rsplit("-", 1)[1]) + 1
        else:
            seq = 1
        return f"{prefix}{seq:05d}"

    @property
    def warranty_expired(self):
        if not self.warranty_until:
            return False
        return self.warranty_until < timezone.now().date()

    @property
    def warranty_days_left(self):
        if not self.warranty_until:
            return None
        return (self.warranty_until - timezone.now().date()).days


class AssetAssignment(models.Model):
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="assignments")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="asset_assignments",
    )
    from_date = models.DateField(default=timezone.now)
    to_date = models.DateField(null=True, blank=True)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-from_date", "-created_at"]
        verbose_name = "Przypisanie"
        verbose_name_plural = "Przypisania"
        indexes = [models.Index(fields=["asset", "to_date"])]

    def __str__(self):
        return f"{self.asset.tag} → {self.user or '—'} ({self.from_date})"

    @property
    def is_active(self):
        return self.to_date is None


class License(models.Model):
    name = models.CharField(max_length=255)
    vendor = models.CharField(max_length=128, blank=True)
    seats_total = models.PositiveIntegerField(default=1)
    seats_used = models.PositiveIntegerField(default=0)
    expires_at = models.DateField(null=True, blank=True)
    key_reference = models.CharField(
        max_length=255, blank=True, help_text="Referencja do klucza (np. sejf, plik)."
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Licencja"
        verbose_name_plural = "Licencje"

    def __str__(self):
        return f"{self.name} ({self.seats_used}/{self.seats_total})"

    @property
    def seats_free(self):
        return max(self.seats_total - self.seats_used, 0)

    @property
    def days_to_expiry(self):
        if not self.expires_at:
            return None
        return (self.expires_at - timezone.now().date()).days
