from django.contrib import admin
from .models import Book, UserBookInteraction, Review

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    """Admin view for the Book model."""
    list_display = ('title', 'google_id', 'published_date')
    search_fields = ('title', 'google_id', 'authors')

@admin.register(UserBookInteraction)
class UserBookInteractionAdmin(admin.ModelAdmin):
    """Admin view for UserBookInteraction."""
    list_display = ('user', 'book', 'status', 'is_favorite')
    list_filter = ('status', 'is_favorite')
    search_fields = ('user__username', 'book__title')

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """Admin view for Review."""
    list_display = ('user', 'book', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('user__username', 'book__title', 'comment')