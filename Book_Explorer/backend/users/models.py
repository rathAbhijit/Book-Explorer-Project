from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils import timezone
from datetime import timedelta
import uuid



# ======================================================
# 🔹 Custom User Manager
# ======================================================
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular user with email instead of username."""
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        extra_fields.setdefault("is_active", True)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a superuser."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_verified", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


# ======================================================
# 🔹 Custom User Model
# ======================================================
class CustomUser(AbstractUser):
    username = None  # disable username field
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=150, blank=True)
    bio = models.TextField(blank=True)
    profile_image = models.ImageField(upload_to="profiles/", blank=True, null=True)

    # Verification and status fields
    is_verified = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    # Replace username with email for authentication
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []  # only email and password are required

    objects = CustomUserManager()

    def __str__(self):
        return self.email or f"User-{self.id}"


# ======================================================
# 🔹 Email OTP Model
# ======================================================
class EmailOTP(models.Model):
    PURPOSE_CHOICES = [
        ("registration", "Registration Verification"),
        ("login", "Login Verification"),
        ("reset", "Password Reset"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="otps")
    otp = models.CharField(max_length=6)
    purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES, default="registration")
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def __str__(self):
        return f"OTP({self.otp}) for {self.user.email} [{self.purpose}]"

    def is_expired(self) -> bool:
        """Check if OTP has expired."""
        return timezone.now() > self.expires_at

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "otp"]),
            models.Index(fields=["expires_at"]),
        ]
