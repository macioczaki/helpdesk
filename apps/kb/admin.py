from django.contrib import admin
from django.utils.html import format_html

from .models import ArticleTag, KnowledgeArticle


@admin.register(ArticleTag)
class ArticleTagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(KnowledgeArticle)
class KnowledgeArticleAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "category", "author", "views", "published_at")
    list_filter = ("status", "category", "tags")
    search_fields = ("title", "summary", "body")
    autocomplete_fields = ("author", "category")
    filter_horizontal = ("tags",)
    readonly_fields = ("views", "created_at", "updated_at", "published_at")
    prepopulated_fields = {"slug": ("title",)}

    fieldsets = (
        (None, {"fields": ("title", "slug", "summary")}),
        ("Treść", {"fields": ("body",)}),
        ("Klasyfikacja", {"fields": ("category", "tags", "status")}),
        ("Meta", {"fields": ("author", "views", "created_at", "updated_at", "published_at")}),
    )

    actions = ["action_publish"]

    @admin.action(description="Opublikuj zaznaczone artykuły")
    def action_publish(self, request, queryset):
        count = 0
        for article in queryset:
            article.publish()
            count += 1
        self.message_user(request, f"Opublikowano {count} artykułów.")