import random
from datetime import timedelta
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from .models import EmailOTP, CustomUser


# ======================================================
# 🔹 Generate OTP
# ======================================================
def generate_otp() -> str:
    """Generate a secure 6-digit OTP."""
    return str(random.randint(100000, 999999))


# ======================================================
# 🔹 Core OTP Sender
# ======================================================
def send_otp_email(user: CustomUser, purpose: str = "verification", otp: str | None = None) -> str:
    """
    Generate (if not provided), store, and send OTP via email.

    Args:
        user (CustomUser): User instance.
        purpose (str): OTP purpose ('registration', 'login', 'reset').
        otp (str, optional): Custom OTP if already generated elsewhere.

    Returns:
        str: The generated or provided OTP.
    """

    # 1️⃣ Clean up old/expired OTPs before creating a new one
    EmailOTP.objects.filter(user=user, expires_at__lt=timezone.now()).delete()

    # 2️⃣ Generate OTP if not given
    otp_code = otp or generate_otp()
    expires_at = timezone.now() + timedelta(minutes=10)

    # 3️⃣ Store OTP in DB
    EmailOTP.objects.create(
        user=user,
        otp=otp_code,
        purpose=purpose,
        expires_at=expires_at,
    )

    # 4️⃣ Prepare email content
    subject_map = {
        "registration": "Book Explorer - Verify Your Email",
        "login": "Book Explorer - Login Verification Code",
        "reset": "Book Explorer - Reset Your Password",
        "verification": "Book Explorer - Verification Code",
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

    # 5️⃣ Send mail (silent fail with debug log)
    try:
        send_mail(subject, message, from_email, [user.email])
    except Exception as e:
        print(f"⚠️ Email send failed for {user.email}: {e}")

    return otp_code


# ======================================================
# 🔹 Registration-Specific Helper
# ======================================================
def send_registration_otp(email: str, name: str = "") -> str:
    """
    Used in pre-verification flow when the user doesn't exist yet.
    Creates a temporary inactive user and sends a registration OTP.
    """
    user, _ = CustomUser.objects.get_or_create(
        email=email,
        defaults={"name": name, "is_active": False, "is_verified": False},
    )
    return send_otp_email(user, purpose="registration")


# ======================================================
# 🔹 OTP Validation Helper (Optional)
# ======================================================
def validate_otp(user: CustomUser, otp_input: str, purpose: str) -> bool:
    """
    Validates an OTP against the EmailOTP table for a given user & purpose.
    Returns True if valid, False otherwise.
    """
    try:
        otp_obj = EmailOTP.objects.filter(user=user, otp=otp_input, purpose=purpose).latest("created_at")
    except EmailOTP.DoesNotExist:
        return False

    if otp_obj.expires_at < timezone.now():
        otp_obj.delete()
        return False

    # Optional cleanup: delete OTP after use
    otp_obj.delete()
    return True
