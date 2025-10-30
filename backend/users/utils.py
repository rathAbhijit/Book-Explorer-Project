import random
from datetime import timedelta
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from .models import EmailOTP, CustomUser


def generate_otp() -> str:
    """Generate a secure 6-digit OTP."""
    return str(random.randint(100000, 999999))


def send_otp_email(user: CustomUser, purpose: str = "verification") -> str:
    """
    Generate, store, and send OTP via email.

    Args:
        user (CustomUser): Existing user instance.
        purpose (str): 'registration', 'login', or 'reset'.

    Returns:
        str: The generated OTP (for debugging or testing).
    """

    # Clean up expired OTPs before creating new one
    EmailOTP.objects.filter(user=user, expires_at__lt=timezone.now()).delete()

    otp_code = generate_otp()
    expires_at = timezone.now() + timedelta(minutes=10)

    EmailOTP.objects.create(
        user=user,
        otp=otp_code,
        purpose=purpose,
        expires_at=expires_at,
    )

    # Dynamic subject & message
    subject_map = {
        "registration": "Book Explorer - Verify Your Email",
        "login": "Book Explorer - Login Verification Code",
        "reset": "Book Explorer - Reset Your Password",
    }
    subject = subject_map.get(purpose, "Book Explorer - Verification Code")

    message = (
        f"Hello {user.name or user.email},\n\n"
        f"Your {purpose} code is: {otp_code}\n"
        "This code will expire in 10 minutes.\n\n"
        "If you didn’t request this, please ignore this email.\n\n"
        "- Book Explorer Team"
    )

    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@bookexplorer.com")

    try:
        send_mail(subject, message, from_email, [user.email])
    except Exception as e:
        print(f"⚠️ Email send failed: {e}")

    return otp_code


def send_registration_otp(email: str, name: str = "") -> str:
    """
    For pre-verification flow: creates a temporary user and sends OTP.
    Used when user does not exist yet.
    """
    user, _ = CustomUser.objects.get_or_create(
        email=email,
        defaults={"name": name, "is_active": False, "is_verified": False},
    )
    return send_otp_email(user, purpose="registration")
