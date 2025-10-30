from celery import shared_task
from django.core.cache import cache
from django.db import transaction
from .models import Book
from .services import generate_and_cache_ai_summary
from .recommender import generate_book_embedding


# ===========================================================
# 🧠 AI Summary Generation Task
# ===========================================================
@shared_task(bind=True, max_retries=3)
def generate_summary_task(self, google_id):
    """Celery task to generate and cache AI summary for a book."""
    print(f"🚀 Starting summary generation for book {google_id}...")

    try:
        summary = generate_and_cache_ai_summary(google_id)
        if summary:
            cache.set(f"book_summary_gemini_{google_id}", summary, 60 * 60 * 24)

            try:
                book = Book.objects.get(google_id=google_id)
                book.ai_summary = summary
                book.save(update_fields=["ai_summary"])
                print(f"✅ Summary saved for {book.title}")
            except Book.DoesNotExist:
                print(f"⚠️ Book {google_id} not found while saving summary.")
        else:
            print(f"⚠️ No summary generated for {google_id}.")
    except Exception as e:
        print(f"🔥 Celery task error for {google_id}: {e}")
        self.retry(exc=e, countdown=10)


# ===========================================================
# 🧩 Embedding Generation Task
# ===========================================================
@shared_task(bind=True, max_retries=2)
def generate_book_embedding_task(self, google_id):
    """Generate and store the vector embedding for a given book asynchronously."""
    print(f"🧩 Generating embedding for book {google_id}...")

    try:
        book = Book.objects.get(google_id=google_id)
        if book.embedding:
            print(f"✅ Embedding already exists for {book.title}")
            return

        vector = generate_book_embedding(book)
        if vector:
            with transaction.atomic():
                book.embedding = vector
                book.save(update_fields=["embedding"])
                cache.set(f"book_embedding_{google_id}", vector, 60 * 60 * 24 * 7)
                print(f"✅ Saved embedding for {book.title}")
        else:
            print(f"⚠️ No embedding generated for {google_id}")

    except Book.DoesNotExist:
        print(f"❌ Book {google_id} not found for embedding generation.")
    except Exception as e:
        print(f"🔥 Embedding generation failed for {google_id}: {e}")
        self.retry(exc=e, countdown=30)


# ===========================================================
# 🎯 Recommendation Generation Task
# ===========================================================
@shared_task(bind=True, max_retries=2)
def generate_recommendations_task(self, user_id, top_n=10):
    from django.contrib.auth import get_user_model
    from .recommender import _compute_recommendations
    from django.core.cache import cache

    User = get_user_model()
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        print(f"⚠️ User {user_id} not found for recommendation generation.")
        return

    print(f"🎯 Generating recommendations for {user.email} ...")
    recs = _compute_recommendations(user, top_n)

    # ✅ Store only book IDs in Redis cache
    book_ids = [b.google_id for b in recs]
    cache.set(f"user_recommendations_{user.id}", book_ids, timeout=60 * 60 * 6)

    print(f"✅ Recommendations cached for {user.email}")
    return book_ids