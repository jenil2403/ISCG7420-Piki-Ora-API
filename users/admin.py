from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class ClinicUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("Clinic", {"fields": ("role", "phone")}),)
    list_display = ("username", "email", "first_name", "last_name", "role", "is_active")
    list_filter = ("role", "is_active")
