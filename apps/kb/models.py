from django.conf import settings
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify


class ArticleTag(models.Model):
    name = models.CharField(max_length=64, unique=True)
    slug = models.SlugField(max_length=64, unique=True, blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Tag"
        verbose_name_plural = "Tagi"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=False)
        super().save(*args, **kwargs)


class KnowledgeArticle(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Szkic"
        PUBLISHED = "PUBLISHED", "Opublikowany"
        ARCHIVED = "ARCHIVED", "Zarchiwizowany"

    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    summary = models.CharField(max_length=512, blank=True)
    body = models.TextField()
    category = models.ForeignKey(
        "tickets.Category",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="kb_articles",
    )
    tags = models.ManyToManyField(ArticleTag, blank=True, related_name="articles")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT)

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="kb_articles_author",
    )
    published_at = models.DateTimeField(null=True, blank=True)
    views = models.PositiveIntegerField(default=0)

    search_vector = SearchVectorField(null=True, editable=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        verbose_name = "Artykuł"
        verbose_name_plural = "Artykuły"
        indexes = [
            models.Index(fields=["status", "-published_at"]),
            models.Index(fields=["category"]),
            models.Index(fields=["search_vector"], name="kb_search_idx"),
            GinIndex(fields=["search_vector"], name="kb_search_vector_gin"),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title, allow_unicode=False)[:255] or "artykul"
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("kb:detail", kwargs={"slug": self.slug})

    def publish(self):
        self.status = self.Status.PUBLISHED
        if not self.published_at:
            self.published_at = timezone.now()
        self.save(update_fields=["status", "published_at", "updated_at"])

    @property
    def is_published(self):
        return self.status == self.Status.PUBLISHED

    def increase_views(self):
        KnowledgeArticle.objects.filter(pk=self.pk).update(views=self.views + 1)