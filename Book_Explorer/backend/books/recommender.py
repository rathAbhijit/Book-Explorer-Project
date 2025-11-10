# books/recommender.py
from typing import List, Optional, Tuple
from openai import OpenAI
from django.conf import settings
from django.core.cache import cache
from .models import Book, UserBookInteraction
import google.generativeai as genai
import math

# Cache timeouts
RECS_CACHE_TTL = 60 * 60 * 6       # 6 hours
EMBEDDING_CACHE_TTL = 60 * 60 * 24 * 7  # 7 days


# --- Embedding generation (OpenAI + Gemini fallback) ---
def generate_book_embedding(book: Book) -> Optional[List[float]]:
    """
    Generate and persist embedding for a Book using OpenAI.
    Fallback to Gemini if OpenAI quota is exceeded or key is invalid.
    """
    if book.embedding and isinstance(book.embedding, list):
        return book.embedding

    text = " ".join(
        filter(
            None,
            [
                book.title,
                ", ".join(book.authors or []),
                book.short_description or book.full_description or "",
            ],
        )
    )

    # --- Attempt OpenAI embedding ---
    try:
        if not getattr(settings, "OPENAI_API_KEY", None):
            raise ValueError("OPENAI_API_KEY missing")

        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        resp = client.embeddings.create(model="text-embedding-3-small", input=text)
        embedding = resp.data[0].embedding

        book.embedding = embedding
        book.save(update_fields=["embedding"])
        cache.set(f"book_embedding_{book.google_id}", embedding, 60 * 60 * 24 * 7)
        print(f"✅ Saved OpenAI embedding for {book.google_id}")
        return embedding

    except Exception as e:
        print(f"⚠️ OpenAI embeddinng failed for {book.google_id}: {e}")

        # --- Gemini fallback ---
        try:
            if not getattr(settings, "GEMINI_API_KEY", None):
                print("⚠️ GEMINI_API_KEY missing. Cannot generate fallback embedding.")
                return None

            genai.configure(api_key=settings.GEMINI_API_KEY)
            response = genai.embed_content(
                model="models/embedding-001",
                content=text,
            )
            embedding = response["embedding"]

            book.embedding = embedding
            book.save(update_fields=["embedding"])
            cache.set(f"book_embedding_{book.google_id}", embedding, 60 * 60 * 24 * 7)
            print(f"✅ Fallback Gemini embedding saved for {book.google_id}")
            return embedding

        except Exception as gem_err:
            print(f"🔥 Gemini fallback failed for {book.google_id}: {gem_err}")
            return None


# --- Vector helpers ---
def _dot(a: List[float], b: List[float]) -> float:
    return sum(x * y for x, y in zip(a, b))

def _norm(a: List[float]) -> float:
    return math.sqrt(sum(x * x for x in a))

def cosine_similarity(a: List[float], b: List[float]) -> float:
    if not a or not b:
        return 0.0
    denom = _norm(a) * _norm(b)
    if denom == 0:
        return 0.0
    return _dot(a, b) / denom


# --- Recommendation logic ---
def _candidate_books(exclude_ids: set, limit: int = 500) -> List[Book]:
    qs = Book.objects.exclude(google_id__in=exclude_ids).order_by("title")[:limit]
    return list(qs)


def _score_by_author_genre(user, candidate: Book, interacted_books: List[Book]) -> float:
    score = 0.0
    interacted_authors = set(a for b in interacted_books for a in (b.authors or []))
    interacted_categories = set(c for b in interacted_books for c in (b.categories or []))

    if any(author in interacted_authors for author in (candidate.authors or [])):
        score += 1.0
    if any(cat in interacted_categories for cat in (candidate.categories or [])):
        score += 0.5

    return score


def _compute_recommendations_for_user(user, top_n: int = 10) -> List[str]:
    interactions = UserBookInteraction.objects.filter(
        user=user,
        status__in=[
            UserBookInteraction.Status.READ,
            UserBookInteraction.Status.READING,
            UserBookInteraction.Status.WANT_TO_READ,
        ],
    ).select_related("book")

    if not interactions.exists():
        qs = Book.objects.order_by("?")[:top_n]
        return [b.google_id for b in qs]

    interacted_books = [i.book for i in interactions]
    interacted_ids = {b.google_id for b in interacted_books}
    candidates = _candidate_books(exclude_ids=interacted_ids, limit=1000)
    if not candidates:
        return []

    emb_cache = {}
    for b in interacted_books:
        emb = cache.get(f"book_embedding_{b.google_id}") or (
            b.embedding if isinstance(b.embedding, list) else None
        )
        if not emb:
            emb = generate_book_embedding(b)
        if emb:
            emb_cache[b.google_id] = emb

    use_embedding = bool(emb_cache)
    user_vector = None
    if use_embedding:
        vecs = list(emb_cache.values())
        length = len(vecs)
        if length:
            user_vector = [sum(col) / length for col in zip(*vecs)]

    scored: List[Tuple[str, float]] = []
    for cand in candidates:
        cand_emb = cache.get(f"book_embedding_{cand.google_id}") or (
            cand.embedding if isinstance(cand.embedding, list) else None
        )
        if not cand_emb and use_embedding:
            cand_emb = generate_book_embedding(cand)

        score = 0.0
        if user_vector and cand_emb:
            score = cosine_similarity(user_vector, cand_emb)
        else:
            score = _score_by_author_genre(user, cand, interacted_books)

        if cand.average_rating:
            score += min(cand.average_rating / 10.0, 0.2)

        scored.append((cand.google_id, score))

    scored_sorted = sorted(scored, key=lambda x: x[1], reverse=True)
    top_ids = [gid for gid, s in scored_sorted[:top_n]]
    return top_ids


def get_user_recommendations(user, top_n=10):
    """
    Returns (status, data):
      - if cached: ("ready", list_of_Book_objects)
      - if not cached: ("processing", {"task_started": True, "task_id": <uuid>})
    """
    cache_key = f"user_recommendations_{user.id}"
    cached = cache.get(cache_key)
    if cached:
        books = list(Book.objects.filter(google_id__in=cached))
        id_to_book = {b.google_id: b for b in books}
        ordered_books = [id_to_book[g] for g in cached if g in id_to_book]
        return {"status": "ready", "books": ordered_books}

    return {"status": "not_ready"}
