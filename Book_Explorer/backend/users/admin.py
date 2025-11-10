from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import CustomUser, EmailOTP


# ======================================================
# 🔹 Custom User Admin
# ======================================================
@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    model = CustomUser
    list_display = ("email", "name", "is_verified", "is_staff", "date_joined", "colored_status")
    list_filter = ("is_verified", "is_staff", "is_superuser", "is_active")
    search_fields = ("email", "name")
    ordering = ("-date_joined",)
    readonly_fields = ("date_joined",)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal Info", {"fields": ("name", "bio", "profile_image")}),
        ("Status", {"fields": ("is_verified", "is_active", "is_staff", "is_superuser")}),
        ("Important Dates", {"fields": ("date_joined",)}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2", "is_verified", "is_active"),
            },
        ),
    )

    def colored_status(self, obj):
        """Visually highlight verification status."""
        color = "green" if obj.is_verified else "red"
        label = "Verified" if obj.is_verified else "Unverified"
        return format_html(f'<b style="color:{color}">{label}</b>')

    colored_status.short_description = "Verification"


# ======================================================
# 🔹 Email OTP Admin
# ======================================================
@admin.register(EmailOTP)
class EmailOTPAdmin(admin.ModelAdmin):
    list_display = ("user_email", "otp", "purpose", "created_at", "expires_at", "is_expired_display")
    list_filter = ("purpose", "created_at", "expires_at")
    search_fields = ("user__email", "otp")
    readonly_fields = ("created_at", "expires_at")

    def user_email(self, obj):
        return obj.user.email

    user_email.short_description = "User Email"

    def is_expired_display(self, obj):
        color = "red" if obj.is_expired() else "green"
        label = "Expired" if obj.is_expired() else "Active"
        return format_html(f'<b style="color:{color}">{label}</b>')

    is_expired_display.short_description = "Status"

    class Meta:
        verbose_name = "Email OTP"
        verbose_name_plural = "Email OTPs"
