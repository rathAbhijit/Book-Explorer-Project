from numpy import sort
import requests
import os
import time
from urllib.parse import quote
from math import ceil
import google.generativeai as genai
from openai import OpenAI
from django.conf import settings
from django.core.cache import cache
from django.db.models import Avg
from sympy import limit

from .models import Review, Book, UserBookInteraction
from .serializers import (
    BookDetailSerializer,
    ReviewMiniSerializer,
    UserBookInteractionMiniSerializer,
)
import io
from typing import List
from pdfminer.high_level import extract_text as pdf_extract_text
from docx import Document as DocxDocument
# --- Configure Gemini ---
try:
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
except Exception:
    print("⚠️ Warning: GEMINI_API_KEY not found or invalid. AI features will fail.")

# -------------------------------
# External API helpers
# -------------------------------

def search_google_books(query, max_results=20, start_index=0):
    """Query the Google Books API with a search term or subject safely."""
    url = "https://www.googleapis.com/books/v1/volumes"
    max_results = min(max_results, 40)  
    safe_query = quote(query)

    params = {
        "q": safe_query,
        "maxResults": max_results,
        "key": getattr(settings, "GOOGLE_BOOKS_API_KEY", None),
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code if e.response else None
        if status_code == 401:
            return {
                "error": "Google Books API returned 401 Unauthorized. Invalid or expired API key.",
                "hint": "Check your GOOGLE_BOOKS_API_KEY in settings or .env file."
            }
        elif status_code == 403:
            return {
                "error": "Google Books API quota exceeded or permission denied.",
                "hint": "Try again later or enable the Books API in your Google Cloud project."
            }
        else:
            return {
                "error": f"Google Books API Error: {str(e)}",
                "hint": "See backend logs for more details."
            }
    except requests.RequestException as e:
        return {
            "error": f"Network or timeout error: {str(e)}",
            "hint": "Ensure your server can reach the Google Books API."
        }
    

def fetch_google_book_by_id(google_id):
    """Get details for a specific book by Google ID from the API."""
    url = f"https://www.googleapis.com/books/v1/volumes/{google_id}"
    params = {"key": getattr(settings, "GOOGLE_BOOKS_API_KEY", None)}
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Google Books API Error fetching ID {google_id}: {e}")
        return None


def get_nyt_bestsellers():
    """Fetch bestseller list from NYT API if valid key is available."""
    api_key = getattr(settings, "NYT_API_KEY", None)
    if not api_key:
        print("⚠️ NYT_API_KEY not set — skipping NYT bestseller fetch.")
        return []

    url = "https://api.nytimes.com/svc/books/v3/lists/current/hardcover-fiction.json"
    params = {"api-key": api_key}
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json().get("results", {}).get("books", [])
        return [
            {
                "title": b.get("title"),
                "authors": [b.get("author")] if b.get("author") else [],
                "thumbnail": b.get("book_image"),
                "description": b.get("description"),
                "rank": b.get("rank"),
                "amazon_url": b.get("amazon_product_url"),
            }
            for b in data
        ]
    except requests.exceptions.HTTPError as e:
        print(f"NYT API Error: {e}")
        return []
    except Exception as e:
        print(f"NYT Bestseller Fetch Error: {e}")
        return []
    


# -------------------------------
# Normalizers (Google + NYT)
# -------------------------------

def normalize_google_book(item):
    """Normalize Google Books API item into unified schema."""
    volume = item.get("volumeInfo", {})
    return {
        "google_id": item.get("id"),
        "title": volume.get("title", "Unknown Title"),
        "authors": volume.get("authors", []),
        "published_date": volume.get("publishedDate"),
        "categories": volume.get("categories", []),
        "thumbnail": (volume.get("imageLinks", {}) or {}).get("thumbnail"),
        "description": volume.get("description"),
        "average_rating": volume.get("averageRating"),
    }

def normalize_nyt_book(item):
    """Normalize NYT bestseller book into unified schema."""
    # ... (rest of function is fine)
    return {
        "google_id": None,
        "title": item.get("title"),
        "authors": [item.get("author")] if item.get("author") else [],
        "thumbnail": item.get("book_image"),
        "description": item.get("description"),
        "amazon_url": item.get("amazon_product_url"),
        "rank": item.get("rank"),
    }

# -------------------------------
# DB caching / get_or_create
# -------------------------------

# IMPROVED: This now saves a more complete record to your database.
def get_or_create_book_details(google_id):
    """
    Check DB for book; if missing, fetch from Google, normalize,
    and save a complete record.
    """
    try:
        return Book.objects.get(google_id=google_id)
    except Book.DoesNotExist:
        data = fetch_google_book_by_id(google_id)
        if not data:
            return None

        normalized_data = normalize_google_book(data)
        
        book, created = Book.objects.update_or_create(
            google_id=google_id,
            defaults={
                "title": normalized_data.get("title", "Unknown Title"),
                "authors": normalized_data.get("authors", []),
                "published_date": normalized_data.get("published_date"),
                "thumbnail_url": normalized_data.get("thumbnail"),
                "short_description": normalized_data.get("description"),
            }
        )
        return book

# -------------------------------
# High-level business logic (with caching)
# -------------------------------

# ADDED: Caching for performance
# ============================================================
# 🔹 Genre Top Books (Improved for Carousel)
# ============================================================
def get_genre_top_books(limit=10):
    """
    Improved version that pulls visually rich, relevant books from
    curated high-interest genres for carousel display.
    Caches results for 6 hours.
    """
    cache_key = "genre_top_books_curated"
    cached = cache.get(cache_key)
    if cached:
        return cached

    # 🎯 Curated high-engagement genres (fiction-heavy & trending)
    curated_genres = [
        "bestseller fiction",
        "modern fantasy",
        "popular thriller",
        "romantic comedy",
        "science fiction novel",
        "historical fiction",
        "graphic novel",
        "inspirational memoir",
        "crime mystery",
        "young adult fiction"
    ]

    books = []
    for genre in curated_genres[:limit]:
        data = search_google_books(f"subject:{genre}", max_results=1)
        if data and "items" in data:
            normalized = [normalize_google_book(i) for i in data["items"]]
            books.extend(normalized)

    # fallback: if Google Books fails, reuse from popular_now
    if not books:
        books = get_popular_now_books(limit=10)

    cache.set(cache_key, books, timeout=60 * 60 * 6)  # 6h
    return books


# ADDED: Caching for performance
# ============================================================
# 🔹 Recently Added Books (Curated for Interest)
# ============================================================
def get_recent_books(limit=10):
    """
    Fetch recent, high-quality books instead of random low-quality results.
    Focuses on fiction & trending genres. Cached for 6 hours.
    """
    cache_key = "recent_books_curated"
    cached_books = cache.get(cache_key)
    if cached_books:
        return cached_books

    # Target genres that constantly have new titles
    queries = [
        "new fiction releases",
        "recent fantasy novels",
        "latest mystery books",
        "2024 popular romance",
        "recent sci-fi releases"
    ]

    books = []
    for q in queries:
        data = search_google_books(q, max_results=3)
        if data and "items" in data:
            normalized = [normalize_google_book(item) for item in data["items"]]
            books.extend(normalized)

    books = books[:limit]
    if not books:
        books = get_popular_now_books(limit=limit)

    cache.set(cache_key, books, 60 * 60 * 6)
    return books

# ADDED: Caching for performance
def get_bestsellers(limit=10):
    """
    Unified bestseller fetcher:
    1️⃣ Try NYT API
    2️⃣ Fallback to Google Books “bestseller OR popular books”
    3️⃣ Fallback to local DB (top-rated)
    """
    cache_key = "bestsellers_combined"
    cached = cache.get(cache_key)
    if cached:
        return cached[:limit]

    books = []

    # 1️⃣ Try NYT API
    nyt_books = get_nyt_bestsellers()
    if nyt_books:
        books = nyt_books[:limit]
        print("✅ Using NYT bestsellers")
    else:
        # 2️⃣ Google Books Fallback
        print("⚠️ Falling back to Google Books bestseller search...")
        google_data = search_google_books("bestseller OR popular books", max_results=limit)
        if google_data and "items" in google_data:
            books = [
                {
                    "google_id": i["id"],
                    "title": i["volumeInfo"].get("title"),
                    "authors": i["volumeInfo"].get("authors", []),
                    "thumbnail": (i["volumeInfo"].get("imageLinks", {}) or {}).get("thumbnail"),
                    "description": i["volumeInfo"].get("description"),
                    "average_rating": i["volumeInfo"].get("averageRating"),
                }
                for i in google_data["items"]
            ]
            print("✅ Using Google Books fallback.")
        else:
            # 3️⃣ Local DB Fallback
            print("⚠️ Falling back to local DB top-rated books.")
            local_books = (
                Book.objects.filter(average_rating__isnull=False)
                .order_by("-average_rating")[:limit]
                .values("google_id", "title", "authors", "thumbnail_url", "average_rating")
            )
            books = list(local_books)

    cache.set(cache_key, books, timeout=60 * 60 * 6)
    return books

# -------------------------------
# AI Summary (Gemini / caching)
# -------------------------------
def generate_and_cache_ai_summary(book_id: str):
    """
    Generate a spoiler-free AI summary using Gemini 2.5 Flash.
    Falls back to OpenAI GPT-4 Turbo if Gemini fails.
    """

    cache_key = f"book_summary_gemini_{book_id}"
    summary = cache.get(cache_key)
    if summary:
        print(f"✅ Cache hit for {book_id}")
        return summary

    try:
        book = Book.objects.get(google_id=book_id)
    except Book.DoesNotExist:
        return "Summary not available because the book is not in our database."

    # --- Prompt ---
    prompt = (
        f"Write a spoiler-free, engaging, and concise summary (around 150 words) "
        f"for the book titled '{book.title}' by {', '.join(book.authors or ['Unknown Author'])}. "
        f"Focus on the tone, main ideas, and emotional appeal — avoid revealing any major plot twists."
    )

    summary = None
    error_message = None

    # --- Try Gemini first ---
    try:
        print(f"⚙️ Using Gemini for '{book.title}'...")
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-2.5-flash")

        response = model.generate_content(prompt)
        if response and getattr(response, "text", None):
            summary = response.text.strip()
            print(f"✅ Gemini succeeded for '{book.title}'")
        else:
            raise ValueError("Gemini returned empty response")

    except Exception as e:
        error_message = str(e)
        print(f"⚠️ Gemini failed: {error_message}")

    # --- Fallback: OpenAI GPT-4 Turbo ---
    if not summary:
        try:
            print(f"🤖 Falling back to OpenAI for '{book.title}'...")
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            completion = client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert book summarizer."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=250,
            )
            summary = completion.choices[0].message.content.strip()
            print(f"✅ OpenAI succeeded for '{book.title}'")
        except Exception as e:
            print(f"🔥 OpenAI fallback also failed: {e}")
            summary = (
                f"'{book.title}' by {', '.join(book.authors or ['Unknown Author'])} "
                "is a remarkable book that explores deep ideas and emotions. "
                "The detailed AI summary is currently unavailable."
            )

    # --- Cache and persist ---
    cache.set(cache_key, summary, 60 * 60 * 24)  # Cache for 24h
    try:
        if not book.ai_summary or book.ai_summary != summary:
            book.ai_summary = summary
            book.save(update_fields=["ai_summary"])
            print(f"💾 Saved AI summary for '{book.title}'")
    except Exception as e:
        print(f"⚠️ DB save error: {e}")

    return summary

# ============================================================
# 🔹 AUTHOR SERVICES
# ============================================================
def fetch_author_details(author_name: str):
    """
    Try fetching author details from Open Library API.
    Falls back to AI-generated bio if not found.
    """
    from django.conf import settings
    from django.core.cache import cache

    cache_key = f"author_detail_{author_name}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    # --- Try Open Library API ---
    try:
        response = requests.get(
            f"https://openlibrary.org/search/authors.json?q={author_name}", timeout=10
        )
        response.raise_for_status()
        data = response.json()

        if not data.get("docs"):
            raise ValueError("No author found in Open Library")

        doc = data["docs"][0]
        author_info = {
            "name": doc.get("name", author_name),
            "birth_date": doc.get("birth_date"),
            "death_date": doc.get("death_date"),
            "top_work": doc.get("top_work"),
            "work_count": doc.get("work_count"),
            "top_subjects": doc.get("top_subjects", [])[:5],
            "bio": doc.get("bio") if isinstance(doc.get("bio"), str) else None,
            "active_years": f"{doc.get('birth_date', '?')} – {doc.get('death_date', '?')}",
        }

    except Exception:
        # --- Fallback to OpenAI GPT bio ---
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        prompt = (
            f"Write a short, factual biography (under 120 words) of the author '{author_name}'. "
            "Include their writing style, themes, and literary significance if known. "
            "Avoid making up data if unknown."
        )
        try:
            completion = client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {"role": "system", "content": "You are a literary historian."},
                    {"role": "user", "content": prompt},
                ],
            )
            bio = completion.choices[0].message.content.strip()
        except Exception:
            bio = "Biography unavailable at the moment."

        author_info = {
            "name": author_name,
            "bio": bio,
            "top_subjects": [],
            "active_years": None,
            "top_work": None,
            "work_count": None,
        }

    cache.set(cache_key, author_info, timeout=60 * 60 * 12)
    return author_info



def paginate_list(items, page=1, page_size=10):
    """
    Slice a Python list manually and return pagination metadata.
    """
    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    sliced = items[start:end]

    has_more = end < total
    next_page = page + 1 if has_more else None

    return {
        "results": sliced,
        "page": page,
        "next_page": next_page,
        "page_size": page_size,
        "total": total,
        "has_more": has_more,
    }


# ============================================================
# 🔹 Explore Page Handler (Unified Logic)
# ============================================================
def get_explore_books(query=None, genre=None, sort=None, limit=50, page=1, page_size=10):
    """
    Unified backend handler for the Explore page (search, genre, sorting) with pagination.
    Default mode returns curated multi-genre sections (Fiction, Novel, Mystery, etc.),
    along with Recent and Popular (Bestseller) sections.
    """

    # Unique cache key per mode and page
    cache_key = f"explore_{query or genre or sort or 'default'}_{page}_{page_size}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    # ==============================
    # 1️⃣ SEARCH MODE — Paginated Search Results
    # ==============================
    if query:
        # true pagination: Google Books supports startIndex
        start_index = (page - 1) * page_size
        data = search_google_books(query, max_results=page_size)
        books = [normalize_google_book(item) for item in data.get("items", [])] if data and "items" in data else []

        total_items = min(data.get("totalItems", len(books)), 200)  # cap to avoid 1M issue
        total_pages = max(1, (total_items + page_size - 1) // page_size)

        result = {
            "mode": "search",
            "data": {
                "results": books,
                "page": page,
                "total_pages": total_pages,
                "total_items": total_items,
            },
        }

        cache.set(cache_key, result, timeout=60 * 60)  # 1 hour cache
        return result

    # ==============================
    # 2️⃣ GENRE MODE — Paginated by Subject
    # ==============================
    if genre:
        start_index = (page - 1) * page_size
        data = search_google_books(f"subject:{genre}", max_results=page_size)
        books = [normalize_google_book(item) for item in data.get("items", [])] if data and "items" in data else []

        total_items = min(data.get("totalItems", len(books)), 200)
        total_pages = max(1, (total_items + page_size - 1) // page_size)

        result = {
            "mode": "genre",
            "data": {
                "results": books,
                "page": page,
                "total_pages": total_pages,
                "total_items": total_items,
            },
        }

        cache.set(cache_key, result, timeout=60 * 60)
        return result

    # ==============================
    # 3️⃣ SORT MODE — Newest / Bestsellers
    # ==============================
    if sort == "newest":
        books = get_recent_books(limit=limit)
    elif sort == "bestsellers":
        books = get_bestsellers(limit=limit)
    else:
        books = []

    if books:
        total_items = len(books)
        total_pages = max(1, (total_items + page_size - 1) // page_size)
        result = {
            "mode": "sorted",
            "data": {
                "results": books,
                "page": page,
                "total_pages": total_pages,
                "total_items": total_items,
            },
        }

        cache.set(cache_key, result, timeout=60 * 60)
        return result

    # ==============================
    # 4️⃣ DEFAULT MODE — BOOKEX-CORE HOME (NO CAROUSEL)
    # ==============================
    print("✨ Building default Explore multi-genre view...")

    sections = {}
    genres = ["Fiction", "Novel", "Mystery", "History", "Science", "Science Fiction"]

    for g in genres:
        data = search_google_books(f"subject:{g}", max_results=7)
        if data and "items" in data:
            sections[g.lower().replace(" ", "_")] = [normalize_google_book(item) for item in data["items"]]

    # Add curated sections
    sections["recent"] = get_recent_books(limit=7)
    sections["popular"] = get_bestsellers(limit=7)

    result = {
        "mode": "default",
        "sections": sections,
    }

    cache.set(cache_key, result, timeout=60 * 60 * 3)  # 3-hour cache
    return result



# ============================================================
# 🔹 BOOK DETAIL (FULL) SERVICE
# ============================================================

def get_full_book_details(book_id, user=None):
    """
    Return complete book details with average rating, reviews,
    and user-specific interaction status.
    Cached for 30 minutes for performance.
    """
    cache_key = f"book_full_detail_{book_id}_{user.id if user else 'anon'}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    try:
        book = Book.objects.get(google_id=book_id)
    except Book.DoesNotExist:
        return {"error": "Book not found."}

    # Base book data
    book_data = BookDetailSerializer(book).data

    # Reviews and average rating
    reviews = Review.objects.filter(book=book).order_by("-created_at")
    review_data = ReviewMiniSerializer(reviews, many=True).data
    avg_rating = reviews.aggregate(avg=Avg("rating"))["avg"]
    book_data["average_rating"] = avg_rating or book.average_rating

    # User interaction (if logged in)
    user_interaction_data = None
    if user and user.is_authenticated:
        interaction = UserBookInteraction.objects.filter(user=user, book=book).first()
        if interaction:
            user_interaction_data = UserBookInteractionMiniSerializer(interaction).data

    result = {
        "book": book_data,
        "reviews": review_data,
        "average_rating": avg_rating or 0,
        "user_interaction": user_interaction_data,
    }

    # Cache for 30 minutes
    cache.set(cache_key, result, timeout=60 * 30)
    return result

# ============================================================
# 🔹 CACHE INVALIDATION HELPERS
# ============================================================

def clear_book_detail_cache(book_id, user_id=None):
    """
    Clears all cached versions of book detail (both user-specific and anonymous).
    """
    cache.delete(f"book_full_detail_{book_id}_anon")
    if user_id:
        cache.delete(f"book_full_detail_{book_id}_{user_id}")

# books/services.py (append near bottom, before cache helpers if you want)

import io
from typing import List
from pdfminer.high_level import extract_text as pdf_extract_text
from docx import Document as DocxDocument
from django.core.cache import cache

# ========== HuggingFace Summarizer (singleton) ==========
_SUMMARIZER = None

def _get_summarizer():
    """
    Lazy-load a local HF summarization pipeline.
    Default: distilbart for speed. Switch to bart-large-cnn if you prefer quality.
    """
    global _SUMMARIZER
    if _SUMMARIZER is not None:
        return _SUMMARIZER

    from transformers import pipeline

    # Light model, good on CPU:
    model_name = "sshleifer/distilbart-cnn-12-6"
    # Heavier but higher quality:
    # model_name = "facebook/bart-large-cnn"

    _SUMMARIZER = pipeline(
        "summarization",
        model=model_name,
        tokenizer=model_name,
        framework="pt",            # Uses torch
        device=-1                  # CPU; set to 0 for GPU
    )
    return _SUMMARIZER


# ========== Text Extraction helpers ==========
def extract_text_from_pdf(fp: io.BytesIO) -> str:
    try:
        return pdf_extract_text(fp)
    except Exception as e:
        raise ValueError(f"Failed to read PDF: {e}")

def extract_text_from_docx(fp: io.BytesIO) -> str:
    try:
        doc = DocxDocument(fp)
        return "\n".join([p.text for p in doc.paragraphs])
    except Exception as e:
        raise ValueError(f"Failed to read DOCX: {e}")

def extract_text_from_txt(fp: io.BytesIO) -> str:
    try:
        data = fp.read()
        try:
            return data.decode("utf-8")
        except UnicodeDecodeError:
            return data.decode("latin-1", errors="ignore")
    except Exception as e:
        raise ValueError(f"Failed to read TXT: {e}")


def extract_text_from_upload(django_file) -> str:
    content_type = django_file.content_type
    buf = io.BytesIO(django_file.read())

    if content_type == "application/pdf":
        return extract_text_from_pdf(buf)
    elif content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return extract_text_from_docx(buf)
    elif content_type == "text/plain":
        return extract_text_from_txt(buf)
    else:
        raise ValueError("Unsupported file type.")


# ========== Chunking + Two-pass summarization ==========
def _split_into_chunks(text: str, max_chars: int = 3000) -> List[str]:
    """
    Conservative chunking by characters. Keeps words intact.
    """
    text = text.strip()
    if not text:
        return []

    chunks = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + max_chars, n)
        # try to cut at nearest sentence end for better quality
        cut = end
        dot = text.rfind(".", start, end)
        qst = text.rfind("?", start, end)
        exc = text.rfind("!", start, end)
        sep = max(dot, qst, exc)
        if sep > start + max_chars * 0.6:
            cut = sep + 1
        chunk = text[start:cut].strip()
        if chunk:
            chunks.append(chunk)
        start = cut
    return chunks

def summarize_text_local(text: str, max_summary_words: int = 250) -> dict:
    """
    Local summarizer using Hugging Face transformer pipeline.
    Handles long inputs safely, with chunking and graceful fallback.
    """
    text = (text or "").strip()
    if not text:
        return {
            "summary": "",
            "input_words": 0,
            "summary_words": 0,
            "compression_ratio": 1.0,
            "chunks": 0,
            "error": "Empty input text."
        }

    summarizer = _get_summarizer()
    words = text.split()
    input_words = len(words)
    target_tokens = max_summary_words * 1.3

    # Hard upper bound on doc size (e.g. 25K chars ≈ 3000–4000 tokens)
    if len(text) > 25000:
        return {
            "summary": None,
            "input_words": input_words,
            "summary_words": 0,
            "compression_ratio": 0,
            "chunks": 0,
            "error": "Document too long for summarization. Please upload a smaller file (<25K characters)."
        }

    # --- Safe chunk splitting
    chunks = _split_into_chunks(text, max_chars=1500)
    summaries = []

    for ch in chunks:
        try:
            res = summarizer(
                ch[:3000],  # truncate for token safety
                max_length=int(min(300, target_tokens)),
                min_length=int(max(50, target_tokens // 3)),
                do_sample=False,
            )
            summaries.append(res[0]["summary_text"].strip())
        except Exception as e:
            print(f"⚠️ Summarization failed on chunk: {e}")
            continue

    if not summaries:
        return {
            "summary": None,
            "input_words": input_words,
            "summary_words": 0,
            "compression_ratio": 0,
            "chunks": len(chunks),
            "error": "All text chunks failed to summarize. Try a smaller file."
        }

    # Combine summaries if multiple chunks
    combined = " ".join(summaries)
    if len(chunks) > 1 and len(combined.split()) > max_summary_words:
        try:
            res2 = summarizer(
                combined[:3000],
                max_length=int(min(400, target_tokens)),
                min_length=int(max(100, target_tokens // 2)),
                do_sample=False,
            )
            final_summary = res2[0]["summary_text"].strip()
        except Exception as e:
            print(f"⚠️ Second pass summarization failed: {e}")
            final_summary = combined
    else:
        final_summary = combined

    summary_words = len(final_summary.split())
    compression_ratio = max(1.0, (input_words / max(1, summary_words)))

    return {
        "summary": final_summary,
        "input_words": input_words,
        "summary_words": summary_words,
        "compression_ratio": round(compression_ratio, 2),
        "chunks": len(chunks),
        "error": None
    }


def summarize_user_upload(django_file, max_summary_words: int = 250):
    """
    Extracts text from uploaded file (PDF/DOCX/TXT) and generates summary safely.
    """
    try:
        text = extract_text_from_upload(django_file)
        text = (text or "").strip()
    except Exception as e:
        print(f"⚠️ Error extracting text: {e}")
        return {
            "summary": None,
            "error": "Could not read the uploaded document. Please check the file format or encoding."
        }

    if not text:
        return {
            "summary": None,
            "error": "The uploaded document is empty or unreadable."
        }

    # Optional pre-truncation to avoid model crashes
    if len(text) > 25000:
        text = text[:25000]
        truncated = True
    else:
        truncated = False

    result = summarize_text_local(text, max_summary_words=max_summary_words)

    # Append truncation note if needed
    if truncated and not result.get("error"):
        result["note"] = "⚠️ Document was truncated to fit model limits (25K characters)."

    return result


# ========== Public service entry points ==========
def summarize_user_text(text: str, max_summary_words: int = 250) -> dict:
    """
    Summarize raw text (no upload). Cached by hash to save time.
    """
    import hashlib
    key = f"user_summary_text_{hashlib.md5((text + str(max_summary_words)).encode('utf-8')).hexdigest()}"
    cached = cache.get(key)
    if cached:
        return {**cached, "cached": True}

    result = summarize_text_local(text, max_summary_words=max_summary_words)
    cache.set(key, result, 60 * 60 * 6)
    return result


# ============================================================
# 🔹 Popular Now Books (Uniform with Carousel)
# ============================================================
def get_popular_now_books(limit=10):

    cache_key = "popular_now_books"
    cached = cache.get(cache_key)
    if cached:
        return cached

    trending_queries = [
        "fiction", "thriller", "fantasy", "romance",
        "science fiction", "mystery", "biography", "history"
    ]

    books = []
    for q in trending_queries:
        data = search_google_books(f"subject:{q}", max_results=2)
        if data and "items" in data:
            normalized = [normalize_google_book(i) for i in data["items"]]
            books.extend(normalized)

    # Trim list to desired limit
    books = books[:limit]
    cache.set(cache_key, books, timeout=60 * 60 * 6)  # 6 hours
    return books
