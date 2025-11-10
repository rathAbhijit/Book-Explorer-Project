from django.urls import path
from .views import (
    # Registration
    RegisterSendOTPView,
    RegisterVerifyOTPView,

    # Login
    LoginOTPView,
    OTPVerifyView,

    # OTP Management
    ResendOTPView,

    # User Profile
    ChangePasswordView,
    UserProfileView,

    # Reset password
    PasswordResetSendOTPView,
    PasswordResetVerifyOTPView,
    PasswordResetConfirmView,
    UserProfileView,

    # Utilities
    test_email_view,
)

app_name = "users"

urlpatterns = [
    # =============================
    # 🔹 Registration Flow
    # =============================
    path("register/send-otp/", RegisterSendOTPView.as_view(), name="register-send-otp"),
    path("register/verify-otp/", RegisterVerifyOTPView.as_view(), name="register-verify-otp"),

    # =============================
    # 🔹 Login Flow
    # =============================
    path("login/", LoginOTPView.as_view(), name="login"),
    path("login/verify-otp/", OTPVerifyView.as_view(), name="login-verify-otp"),

    # =============================
    # 🔹 OTP Management
    # =============================
    path("resend-otp/", ResendOTPView.as_view(), name="resend-otp"),

    # =============================
    # 🔹 User Profile & Account
    # =============================
    # ✅ Add this instead
    path("profile/", UserProfileView.as_view(), name="user-profile"),
    path("change-password/", ChangePasswordView.as_view(), name="change-password"),

    # =============================
    # 🔹 Email Test (for debugging)
    # =============================
    path("test-email/", test_email_view, name="test-email"),

    # Password reset
    path("password/reset/send-otp/", PasswordResetSendOTPView.as_view(), name="password-reset-send-otp"),
    path("password/reset/verify-otp/", PasswordResetVerifyOTPView.as_view(), name="password-reset-verify-otp"),
    path("password/reset/confirm/", PasswordResetConfirmView.as_view(), name="password-reset-confirm"),

]
