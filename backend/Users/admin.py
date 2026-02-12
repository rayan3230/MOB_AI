from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['username', 'user_email', 'user_role', 'is_staff']
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('user_code', 'user_name', 'user_role', 'user_email', 'user_visibility')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('user_name', 'user_role', 'user_email', 'user_visibility')}),
    )
