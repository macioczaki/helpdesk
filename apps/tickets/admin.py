from django.contrib import admin

from .models import Category, Ticket


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "parent", "default_priority")
    list_filter = ("default_priority",)
    search_fields = ("name",)


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("number", "title", "status", "priority", "category", "created_by", "assigned_to", "created_at")
    list_filter = ("status", "priority", "category")
    search_fields = ("number", "title", "description")
    readonly_fields = ("number", "created_at", "updated_at", "resolved_at", "closed_at")
    autocomplete_fields = ("created_by", "assigned_to")
    date_hierarchy = "created_at"