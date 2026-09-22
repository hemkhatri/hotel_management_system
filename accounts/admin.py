from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    # Display the custom phone number alongside default fields in the user list
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "phone_number",
        "is_staff",
    )
    
    # Extend search fields to allow searching by phone number
    search_fields = BaseUserAdmin.search_fields + ("phone_number",)

    # Inject the phone_number field into the detail editing page
    # This safely appends it to the 'Personal info' section without breaking standard User fields
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Additional Contact Information", {
            "fields": ("phone_number",)
        }),
    )

    # Inject the phone_number field into the user creation page
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("Additional Contact Information", {
            "fields": ("phone_number",)
        }),
    )
