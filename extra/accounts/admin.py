from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import UserModel

class CustomUserAdmin(BaseUserAdmin):
    # Columns shown in the user table list
    list_display = ['username', 'email', 'phone_number', 'is_staff', 'is_active']
    
    # Injects phone number into the edit user form view
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('phone_number',)}),
    )
    
    # Injects phone number into the create user form view
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('phone_number',)}),
    )

# Explicitly register the model and admin class at the end
admin.site.register(UserModel, CustomUserAdmin)
