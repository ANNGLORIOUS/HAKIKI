from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "phone_verified", "email_verified", "role", "reputation")
    fieldsets = UserAdmin.fieldsets + (("Scam Watch", {"fields": ("phone", "phone_verified", "email_verified", "role", "reputation")}),)
