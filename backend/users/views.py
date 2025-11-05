from django.contrib.auth import get_user_model, authenticate
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from backend.books.models import UserBookInteraction, Review
from .serializers import LoginSendOTPSerializer, LoginVerifyOTPSerializer, BookSerializer, ReviewSerializer
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken
from .models import EmailOTP
import random
from django.utils import timezone

from .serializers import (
    RegisterSerializer,
    OTPVerifySerializer,
    UserProfileSerializer,
    ChangePasswordSerializer,
    ResendOTPSerializer,
    UserDashboardSerializer,
)
from .services import get_user_dashboard_data
from .models import CustomUser, EmailOTP
from .utils import send_otp_email, send_registration_otp

User = get_user_model()


# ======================================================
# 🔹 Registration (Send OTP)
# ======================================================
class RegisterSendOTPView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get("email")
        name = request.data.get("name", "")
        password = request.data.get("password")

        if not email or not password:
            return Response({"detail": "Email and password required."}, status=400)

        if CustomUser.objects.filter(email=email, is_verified=True).exists():
            return Response({"detail": "Email already registered."}, status=400)

        otp = send_registration_otp(email, name)
        return Response(
            {"detail": f"OTP sent to {email}. Complete verification to finish registration."},
            status=200,
        )


# ======================================================
# 🔹 Registration Verify OTP
# ======================================================
class RegisterVerifyOTPView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get("email")
        otp = request.data.get("otp")
        password = request.data.get("password")

        if not all([email, otp, password]):
            return Response({"detail": "Email, OTP, and password are required."}, status=400)

        try:
            user = CustomUser.objects.get(email=email)
            otp_obj = EmailOTP.objects.filter(user=user, otp=otp).latest("created_at")
        except (CustomUser.DoesNotExist, EmailOTP.DoesNotExist):
            return Response({"detail": "Invalid email or OTP."}, status=400)

        if otp_obj.is_expired():
            return Response({"detail": "OTP expired."}, status=400)

        # ✅ Finalize registration
        user.set_password(password)
        user.is_active = True
        user.is_verified = True
        user.save()
        EmailOTP.objects.filter(user=user).delete()

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "detail": "Registration complete.",
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            },
            status=200,
        )

# ======================================================
# 🔹 Login via OTP (Step 1)
# ======================================================
class LoginOTPView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSendOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        # ✅ Use utility function (handles DB + expiry)
        send_otp_email(user, purpose="login")

        return Response(
            {"detail": f"OTP sent to {user.email}. Verify to complete login."},
            status=200,
        )
    

class OTPVerifyView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginVerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "detail": "Login successful.",
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            },
            status=200,
        )



# ======================================================
# 🔹 PASSWORD RESET: Send OTP
# ======================================================
class PasswordResetSendOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"detail": "Email required."}, status=400)

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            return Response({"detail": "No account found with this email."}, status=404)

        send_otp_email(user, purpose="reset")
        return Response({"detail": f"Password reset OTP sent to {email}."}, status=200)


# ======================================================
# 🔹 PASSWORD RESET: Verify OTP
# ======================================================
class PasswordResetVerifyOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        otp = request.data.get("otp")

        if not all([email, otp]):
            return Response({"detail": "Email and OTP required."}, status=400)

        try:
            user = CustomUser.objects.get(email=email)
            otp_obj = EmailOTP.objects.filter(user=user, otp=otp, purpose="reset").latest("created_at")
        except (CustomUser.DoesNotExist, EmailOTP.DoesNotExist):
            return Response({"detail": "Invalid email or OTP."}, status=400)

        if otp_obj.is_expired():
            return Response({"detail": "OTP expired."}, status=400)

        EmailOTP.objects.filter(user=user, purpose="reset").delete()
        request.session["reset_user_id"] = user.id
        return Response({"detail": "OTP verified. You may now set a new password."}, status=200)


# ======================================================
# 🔹 PASSWORD RESET: Confirm (Set new password)
# ======================================================
class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        user_id = request.session.get("reset_user_id")
        new_password = request.data.get("new_password")

        if not user_id:
            return Response({"detail": "Session expired or invalid."}, status=400)
        if not new_password:
            return Response({"detail": "New password required."}, status=400)

        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response({"detail": "User not found."}, status=404)

        user.set_password(new_password)
        user.save()
        request.session.pop("reset_user_id", None)
        return Response({"detail": "Password reset successful."}, status=200)


# ======================================================
# 🔹 Resend OTP
# ======================================================
class ResendOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResendOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        send_otp_email(user)
        return Response({"detail": "New OTP sent to your email."}, status=200)


# ======================================================
# 🔹 Profile
# ======================================================
class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Unified profile endpoint:
    - GET: Returns full user profile + stats
    - PATCH: Updates user profile (name, bio, image)
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserProfileSerializer

    def get_object(self):
        return self.request.user

    def get(self, request, *args, **kwargs):
        user = request.user

        # Basic profile info
        profile_data = self.get_serializer(user, context={"request": request}).data

        # Stats
        interactions = UserBookInteraction.objects.filter(user=user)
        stats = {
            "total_books": interactions.count(),
            "want_to_read": interactions.filter(status="WTR").count(),
            "reading": interactions.filter(status="RDG").count(),
            "read": interactions.filter(status="RD").count(),
            "favorites": interactions.filter(is_favorite=True).count(),
            "reviews": Review.objects.filter(user=user).count(),
        }

        # Preview data
        recent_reviews = Review.objects.filter(user=user).order_by("-created_at")[:3]
        favorite_books = interactions.filter(is_favorite=True)[:3]

        profile_data["stats"] = stats
        profile_data["recent_reviews"] = ReviewSerializer(recent_reviews, many=True).data
        profile_data["favorite_books"] = [
            BookSerializer(i.book).data for i in favorite_books
        ]

        return Response(profile_data, status=status.HTTP_200_OK)


# ======================================================
# 🔹 Change Password
# ======================================================
class ChangePasswordView(generics.UpdateAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


# ======================================================
# 🔹 Test Email
# ======================================================
@api_view(["POST"])
@permission_classes([AllowAny])
def test_email_view(request):
    email = request.data.get("email")
    if not email:
        return Response({"detail": "Email required."}, status=400)

    try:
        user, _ = CustomUser.objects.get_or_create(email=email, defaults={"is_active": True})
        otp = send_otp_email(user)
        return Response({"detail": f"Test OTP sent to {email}", "otp": otp}, status=200)
    except Exception as e:
        return Response({"detail": str(e)}, status=500)

