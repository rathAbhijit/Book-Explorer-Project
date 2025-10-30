import numpy as np
import pandas as pd
from openai import OpenAI
from django.conf import settings
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from django.core.cache import cache
from .models import Book, UserBookInteraction


# ===========================================================
# 🧠 Recommendation Entry Point
# ===========================================================
def get_user_recommendations(user, top_n=10):
    """
    Return recommendations if ready; else start background generation.
    """
    from .tasks import generate_recommendations_task  # lazy import

    cache_key = f"user_recommendations_{user.id}"
    cached = cache.get(cache_key)
    if cached:
        # ✅ Convert cached IDs into Book objects
        books = list(Book.objects.filter(google_id__in=cached))
        return {"status": "ready", "books": books}

    # Otherwise, trigger background job
    task = generate_recommendations_task.delay(user.id, top_n)
    return {
        "status": "processing",
        "message": "Generating recommendations. Please retry in a few seconds.",
        "task_id": task.id,
    }


# ===========================================================
# 📊 TF-IDF Caching Setup
# ===========================================================
_book_tfidf = None
_book_sim = None
_book_index = None


def _prepare_tfidf():
    """Prepare TF-IDF similarity matrix for all books (cached globally)."""
    global _book_tfidf, _book_sim, _book_index

    books = list(
        Book.objects.all().values(
            "google_id", "title", "authors", "categories", "short_description"
        )
    )
    if not books:
        return None, None, None

    df = pd.DataFrame(books)
    df["text"] = (
        df["title"].fillna("")
        + " "
        + df["authors"].apply(lambda a: " ".join(a) if isinstance(a, list) else str(a))
        + " "
        + df["categories"].apply(lambda c: " ".join(c) if isinstance(c, list) else str(c))
        + " "
        + df["short_description"].fillna("")
    )

    vectorizer = TfidfVectorizer(stop_words="english", max_features=5000)
    tfidf = vectorizer.fit_transform(df["text"])
    sim = cosine_similarity(tfidf)

    _book_tfidf, _book_sim, _book_index = (
        df,
        sim,
        {gid: idx for idx, gid in enumerate(df["google_id"])},
    )
    return _book_tfidf, _book_sim, _book_index


# ===========================================================
# 🔥 Heavy Recommendation Computation (used by Celery)
# ===========================================================
def _compute_recommendations(user, top_n=10):
    """
    Heavy computation function (called inside Celery task).
    """
    global _book_tfidf, _book_sim, _book_index

    if _book_tfidf is None:
        _prepare_tfidf()

    interactions = UserBookInteraction.objects.filter(
        user=user, status__in=["RD", "RDG", "WTR"]
    )
    if not interactions.exists():
        return list(Book.objects.all().order_by("?")[:top_n])

    scores = np.zeros(len(_book_tfidf))
    for inter in interactions:
        gid = inter.book.google_id
        if gid not in _book_index:
            continue
        idx = _book_index[gid]
        scores += _book_sim[idx]

    interacted_ids = set(interactions.values_list("book__google_id", flat=True))
    _book_tfidf["score"] = scores
    recs = _book_tfidf[
        ~_book_tfidf["google_id"].isin(interacted_ids)
    ].sort_values("score", ascending=False)
    top_ids = recs["google_id"].head(top_n).tolist()

    return list(Book.objects.filter(google_id__in=top_ids))


# ===========================================================
# 🧩 Embedding Generator
# ===========================================================
def generate_book_embedding(book):
    """
    Generate and store an embedding vector for a book using OpenAI embeddings.
    Uses title, authors, and description for context.
    """
    if book.embedding and isinstance(book.embedding, list):
        print(f"✅ Embedding already exists for '{book.title}', skipping regeneration.")
        return book.embedding

    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    text = (
        f"Title: {book.title}\n"
        f"Authors: {', '.join(book.authors or [])}\n"
        f"Description: {book.short_description or ''}"
    )

    try:
        print(f"🔹 Generating embedding for: {book.title}")
        response = client.embeddings.create(model="text-embedding-3-small", input=text)
        embedding = response.data[0].embedding
        book.embedding = embedding
        book.save(update_fields=["embedding"])
        print(f"✅ Embedding saved for '{book.title}' ({len(embedding)} dimensions).")
        return embedding
    except Exception as e:
        print(f"⚠️ Failed to generate embedding for '{book.title}': {e}")
        return None
