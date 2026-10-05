from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import Department, User


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "building", "floor")
    search_fields = ("name", "building")


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("username", "email", "first_name", "last_name", "role", "department", "is_active")
    list_filter = ("role", "department", "is_active", "is_staff")
    search_fields = ("username", "email", "first_name", "last_name")
    ordering = ("username",)

    fieldsets = DjangoUserAdmin.fieldsets + (
        ("Profil urzędu", {"fields": ("role", "department", "phone", "room")}),
    )
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        ("Profil urzędu", {"fields": ("role", "department", "phone", "room")}),
    )