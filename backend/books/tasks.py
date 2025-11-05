from celery import shared_task
from django.core.cache import cache
from django.db import transaction
from django.contrib.auth import get_user_model
from .models import Book
from .services import generate_and_cache_ai_summary
from .recommender import generate_book_embedding, _compute_recommendations_for_user

User = get_user_model()


# ===========================================================
# 🧠 AI Summary Generation Task
# ===========================================================
@shared_task(bind=True, max_retries=3)
def generate_summary_task(self, google_id):
    """Celery task to generate and cache AI summary for a book."""
    print(f"🚀 [Celery] Starting summary generation for book {google_id}...")

    try:
        summary = generate_and_cache_ai_summary(google_id)
        if summary:
            cache.set(f"book_summary_gemini_{google_id}", summary, 60 * 60 * 24)
            try:
                book = Book.objects.get(google_id=google_id)
                book.ai_summary = summary
                book.save(update_fields=["ai_summary"])
                print(f"✅ [Celery] Summary saved for '{book.title}' ({google_id})")
            except Book.DoesNotExist:
                print(f"⚠️ [Celery] Book {google_id} not found while saving summary.")
        else:
            print(f"⚠️ [Celery] No summary generated for {google_id}.")
    except Exception as e:
        print(f"🔥 [Celery] Error in summary generation for {google_id}: {e}")
        self.retry(exc=e, countdown=15)


# ===========================================================
# 🧩 Embedding Generation Task (OpenAI + Gemini Fallback)
# ===========================================================
@shared_task(bind=True, max_retries=2)
def generate_book_embedding_task(self, google_id):
    """Generate and store vector embedding for a given book asynchronously."""
    print(f"🧩 [Celery] Generating embedding for book {google_id}...")

    try:
        book = Book.objects.get(google_id=google_id)
    except Book.DoesNotExist:
        print(f"❌ [Celery] Book {google_id} not found for embedding generation.")
        return

    try:
        vector = generate_book_embedding(book)
        if vector:
            with transaction.atomic():
                book.embedding = vector
                book.save(update_fields=["embedding"])
                cache.set(f"book_embedding_{google_id}", vector, 60 * 60 * 24 * 7)
                print(f"✅ [Celery] Embedding saved for '{book.title}' ({google_id})")
        else:
            print(f"⚠️ [Celery] Embedding not generated for {google_id}. Possibly API key or quota issue.")
    except Exception as e:
        print(f"🔥 [Celery] Embedding generation failed for {google_id}: {e}")
        self.retry(exc=e, countdown=30)


# ===========================================================
# 🎯 Recommendation Generation Task
# ===========================================================
@shared_task(bind=True, max_retries=2)
def generate_recommendations_task(self, user_id, top_n=10):
    """
    Compute recommendations for a user and cache their google_ids.
    Adds detailed debug logs to show whether OpenAI, Gemini, or heuristics were used.
    """
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        print(f"❌ [Celery] User {user_id} not found for recommendations.")
        return []

    print(f"🎯 [Celery] Generating recommendations for {user.email}...")

    try:
        top_ids = _compute_recommendations_for_user(user, top_n=top_n)

        cache_key = f"user_recommendations_{user.id}"
        cache.set(cache_key, top_ids, timeout=60 * 60 * 6)  # 6 hours

        # --- Smart Log Context ---
        used_embeddings = any(
            Book.objects.filter(google_id=i, embedding__isnull=False).exists()
            for i in top_ids
        )
        if not used_embeddings:
            log_source = "HEURISTIC fallback (author/genre)"
        else:
            log_source = "OpenAI/Gemini embeddings"

        print(f"✅ [Celery] Recommendations cached for {user.email} ({len(top_ids)} items). Source: {log_source}")
        return top_ids

    except Exception as exc:
        print(f"🔥 [Celery] Recommendation generation failed for {user.email}: {exc}")
        raise self.retry(exc=exc, countdown=60)
