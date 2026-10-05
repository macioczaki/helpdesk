from django.contrib import admin

from .models import Asset, AssetAssignment, AssetCategory, License, Location


@admin.register(AssetCategory)
class AssetCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "parent")
    search_fields = ("name",)


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("building", "floor", "room")
    search_fields = ("building", "floor", "room")


class AssetAssignmentInline(admin.TabularInline):
    model = AssetAssignment
    extra = 0
    readonly_fields = ("created_at",)
    autocomplete_fields = ("user",)


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = (
        "tag",
        "name",
        "type",
        "status",
        "location",
        "assigned_to",
        "warranty_until",
    )
    list_filter = ("type", "status", "category", "location")
    search_fields = ("tag", "name", "serial_number", "manufacturer", "model_name")
    autocomplete_fields = ("assigned_to", "category")
    readonly_fields = ("tag", "created_at", "updated_at")
    inlines = [AssetAssignmentInline]
    date_hierarchy = "created_at"


@admin.register(License)
class LicenseAdmin(admin.ModelAdmin):
    list_display = ("name", "vendor", "seats_used", "seats_total", "expires_at")
    list_filter = ("vendor",)
    search_fields = ("name", "vendor")
    readonly_fields = ("created_at",)
