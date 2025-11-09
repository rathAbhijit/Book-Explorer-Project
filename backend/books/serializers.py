from rest_framework import serializers
from .models import Book, UserBookInteraction, Review


# ============================================================
# 🔹 Book Serializer (Basic)
# ============================================================
class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = [
            'google_id',
            'title',
            'authors',
            'published_date',
            'thumbnail_url',
            'short_description',
        ]


# ============================================================
# 🔹 UserBookInteraction Serializer
# ============================================================
class UserBookInteractionSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.name')
    book = serializers.PrimaryKeyRelatedField(queryset=Book.objects.all())

    class Meta:
        model = UserBookInteraction
        fields = ["user", "book", "status", "is_favorite"]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['book'] = BookSerializer(instance.book).data
        return representation


# ============================================================
# 🔹 Review Serializer
# ============================================================
class ReviewSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.name", read_only=True)

    class Meta:
        model = Review
        fields = ["id", "book", "user", "username", "rating", "comment", "created_at"]
        read_only_fields = ["user", "book"]

# ============================================================
# 🔹 Author Serializer
# ============================================================
class AuthorSerializer(serializers.Serializer):
    name = serializers.CharField()
    bio = serializers.CharField(allow_blank=True, required=False)
    top_subjects = serializers.ListField(child=serializers.CharField(), required=False)
    active_years = serializers.CharField(allow_blank=True, required=False)
    birth_date = serializers.CharField(allow_blank=True, required=False)
    death_date = serializers.CharField(allow_blank=True, required=False)
    top_work = serializers.CharField(allow_blank=True, required=False)
    work_count = serializers.IntegerField(required=False)


# ============================================================
# 🔹 Book Detail (Extended) Serializers
# ============================================================
class BookDetailSerializer(serializers.ModelSerializer):
    """Extended book detail for full info view."""
    class Meta:
        model = Book
        fields = [
            "google_id",
            "title",
            "authors",
            "published_date",
            "categories",
            "thumbnail_url",
            "full_description",
            "short_description",
            "ai_summary",
            "average_rating",
        ]


class ReviewMiniSerializer(serializers.ModelSerializer):
    """Simplified version of Review for detail page."""
    username = serializers.CharField(source="user.name", read_only=True)

    class Meta:
        model = Review
        fields = ["id", "username", "rating", "comment", "created_at"]


class UserBookInteractionSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.name')
    book = serializers.PrimaryKeyRelatedField(queryset=Book.objects.all())
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = UserBookInteraction
        fields = ["user", "book", "status", "status_display", "is_favorite"]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['book'] = BookSerializer(instance.book).data
        return representation
# books/serializers.py (append at bottom)

class SummarizeTextSerializer(serializers.Serializer):
    text = serializers.CharField(allow_blank=False, trim_whitespace=False)
    max_summary_words = serializers.IntegerField(required=False, min_value=30, max_value=1200, default=250)

class SummarizeUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    max_summary_words = serializers.IntegerField(required=False, min_value=30, max_value=1200, default=250)

    def validate_file(self, f):
        allowed = {"application/pdf", "text/plain", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
        if f.content_type not in allowed:
            raise serializers.ValidationError("Unsupported file type. Allowed: PDF, TXT, DOCX.")
        if f.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("File too large (max 10 MB).")
        return f

class UserBookInteractionMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserBookInteraction
        fields = ["status", "is_favorite"]
