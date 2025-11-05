from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


# ============================================================
# 🔹 Book Model
# ============================================================
class Book(models.Model):
    google_id = models.CharField(max_length=100, unique=True, primary_key=True)
    title = models.CharField(max_length=255)
    authors = models.JSONField(default=list)
    published_date = models.CharField(max_length=20, null=True, blank=True)
    categories = models.JSONField(default=list, blank=True)
    thumbnail_url = models.URLField(max_length=500, null=True, blank=True)
    full_description = models.TextField(null=True, blank=True)
    short_description = models.TextField(null=True, blank=True)
    ai_summary = models.TextField(null=True, blank=True)
    average_rating = models.FloatField(null=True, blank=True)

    # 🔹 Persistent vector embedding for recommendations
    embedding = models.JSONField(null=True, blank=True)

    def __str__(self):
        return self.title

    def has_embedding(self):
        """Check if this book has an embedding stored."""
        return bool(self.embedding)


# ============================================================
# 🔹 User ↔ Book Interaction Model
# ============================================================
class UserBookInteraction(models.Model):
    class Status(models.TextChoices):
        WANT_TO_READ = "WTR", "Want to Read"
        READING = "RDG", "Reading"
        READ = "RD", "Read"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="interactions",
    )
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="interactions")
    status = models.CharField(max_length=3, choices=Status.choices, null=True, blank=True)
    is_favorite = models.BooleanField(default=False)

    class Meta:
        unique_together = ("user", "book")

    def __str__(self):
        return f"{self.user.name or self.user.email} - {self.book.title}"


# ============================================================
# 🔹 Review Model
# ============================================================
class Review(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="reviews")
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "book")
        ordering = ["-created_at"]

    def __str__(self):
        return f"Review for {self.book.title} by {self.user.name or self.user.email}"

    @property
    def short_comment(self):
        """Return first 80 chars for previews."""
        return (self.comment[:80] + "...") if self.comment and len(self.comment) > 80 else self.comment
