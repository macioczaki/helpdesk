from django.contrib import admin

from .models import (
    SLA,
    Category,
    Ticket,
    TicketAttachment,
    TicketComment,
    TicketHistory,
)


class TicketCommentInline(admin.TabularInline):
    model = TicketComment
    extra = 0
    readonly_fields = ("created_at",)


class TicketAttachmentInline(admin.TabularInline):
    model = TicketAttachment
    extra = 0
    readonly_fields = ("created_at", "original_name")


# --- Rejestracje ---


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "parent", "default_priority")
    list_filter = ("default_priority",)
    search_fields = ("name",)


@admin.register(SLA)
class SLAAdmin(admin.ModelAdmin):
    list_display = ("priority", "response_minutes", "resolve_minutes")


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = (
        "number",
        "title",
        "status",
        "priority",
        "category",
        "created_by",
        "assigned_to",
        "created_at",
    )
    list_filter = ("status", "priority", "category")
    search_fields = ("number", "title", "description")
    readonly_fields = ("number", "created_at", "updated_at", "resolved_at", "closed_at")
    autocomplete_fields = ("created_by", "assigned_to")
    date_hierarchy = "created_at"
    inlines = [TicketCommentInline, TicketAttachmentInline]


@admin.register(TicketComment)
class TicketCommentAdmin(admin.ModelAdmin):
    list_display = ("ticket", "author", "is_internal", "created_at")
    list_filter = ("is_internal",)
    search_fields = ("body", "ticket__number")


@admin.register(TicketHistory)
class TicketHistoryAdmin(admin.ModelAdmin):
    list_display = ("ticket", "field", "old_value", "new_value", "changed_by", "changed_at")
    list_filter = ("field",)
    search_fields = ("ticket__number",)
    readonly_fields = ("ticket", "field", "old_value", "new_value", "changed_by", "changed_at")


@admin.register(TicketAttachment)
class TicketAttachmentAdmin(admin.ModelAdmin):
    list_display = ("original_name", "ticket", "uploaded_by", "created_at")
    search_fields = ("original_name", "ticket__number")
