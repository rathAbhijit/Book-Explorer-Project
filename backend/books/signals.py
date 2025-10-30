from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Review, UserBookInteraction
from .services import clear_book_detail_cache


# ------------------------------------------------------------
# 🔹 When a review changes → clear cache
# ------------------------------------------------------------
@receiver([post_save, post_delete], sender=Review)
def clear_cache_on_review_change(sender, instance, **kwargs):
    book_id = instance.book.google_id
    user_id = instance.user.id
    clear_book_detail_cache(book_id, user_id=None)


# ------------------------------------------------------------
# 🔹 When user-book interaction changes → clear cache
# ------------------------------------------------------------
@receiver([post_save, post_delete], sender=UserBookInteraction)
def clear_cache_on_interaction_change(sender, instance, **kwargs):
    book_id = instance.book.google_id
    user_id = instance.user.id
    clear_book_detail_cache(book_id, user_id)
