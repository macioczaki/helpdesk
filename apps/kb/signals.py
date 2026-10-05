from django.contrib.postgres.search import SearchVector
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import KnowledgeArticle


@receiver(post_save, sender=KnowledgeArticle)
def update_search_vector(sender, instance, **kwargs):
    KnowledgeArticle.objects.filter(pk=instance.pk).update(
        search_vector=(
            SearchVector("title", weight="A", config="simple")
            + SearchVector("summary", weight="B", config="simple")
            + SearchVector("body", weight="C", config="simple")
        )
    )
