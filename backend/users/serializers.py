from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from django.conf import settings
from .models import EmailOTP
from django.utils import timezone
from backend.books.serializers import BookSerializer, ReviewSerializer
from backend.books.models import UserBookInteraction

User = get_user_model()


# ======================================================
# 🔹 Registration Serializer
# ======================================================
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ("email", "name", "password", "password2")

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password2")
        password = validated_data.pop("password")
        user = User.objects.create_user(password=password, **validated_data)
        return user


# ======================================================
# 🔹 OTP Verification Serializer
# ======================================================
class OTPVerifySerializer(serializers.Serializer):
    otp = serializers.CharField(max_length=6)

    def validate(self, attrs):
        user = self.context["user"]
        otp_input = attrs.get("otp")

        try:
            otp_obj = EmailOTP.objects.filter(user=user, otp=otp_input).latest("created_at")
        except EmailOTP.DoesNotExist:
            raise serializers.ValidationError("Invalid OTP.")

        if otp_obj.is_expired():
            raise serializers.ValidationError("OTP expired.")

        otp_obj.delete()  # cleanup
        return attrs


# ======================================================
# 🔹 User Profile Serializer
# ======================================================
class UserProfileSerializer(serializers.ModelSerializer):
    profile_image_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "name",
            "bio",
            "profile_image",
            "profile_image_url",
            "is_verified",
            "date_joined",
        )
        read_only_fields = ("email", "is_verified", "date_joined")

    def get_profile_image_url(self, obj):
        """
        Return absolute URL for profile image.
        """
        if obj.profile_image:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.profile_image.url)
            return f"{settings.MEDIA_URL}{obj.profile_image.url}"
        return None

    def update(self, instance, validated_data):
        """
        Allow partial profile updates.
        """
        instance.name = validated_data.get("name", instance.name)
        instance.bio = validated_data.get("bio", instance.bio)
        profile_image = validated_data.get("profile_image")
        if profile_image:
            instance.profile_image = profile_image
        instance.save()
        return instance


# ======================================================
# 🔹 Change Password Serializer
# ======================================================
class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, validators=[validate_password])

    def validate(self, attrs):
        user = self.context["request"].user
        if not user.check_password(attrs["old_password"]):
            raise serializers.ValidationError({"old_password": "Old password is incorrect."})
        return attrs

    def update(self, instance, validated_data):
        instance.set_password(validated_data["new_password"])
        instance.save()
        return instance


# ======================================================
# 🔹 Resend OTP Serializer
# ======================================================
class ResendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate(self, attrs):
        email = attrs["email"]
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found.")

        if user.is_verified:
            raise serializers.ValidationError("Email already verified.")

        attrs["user"] = user
        return attrs

class UserDashboardSerializer(serializers.Serializer):
    user = UserProfileSerializer(read_only=True)
    stats = serializers.DictField()
    recent_interactions = serializers.SerializerMethodField()
    recent_reviews = serializers.SerializerMethodField()

    def get_recent_interactions(self, obj):
        return [
            {
                "book": BookSerializer(interaction.book).data,
                "status": interaction.status,
                "is_favorite": interaction.is_favorite,
            }
            for interaction in obj["recent_interactions"]
        ]

    def get_recent_reviews(self, obj):
        return [
            ReviewSerializer(review).data
            for review in obj["recent_reviews"]
        ]