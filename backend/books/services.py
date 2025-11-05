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

from .models import Review, Book, UserBookInteraction
from .serializers import (
    BookDetailSerializer,
    ReviewMiniSerializer,
    UserBookInteractionMiniSerializer,
)

# --- Configure Gemini ---
try:
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
except Exception:
    print("⚠️ Warning: GEMINI_API_KEY not found or invalid. AI features will fail.")

# -------------------------------
# External API helpers
# -------------------------------

def search_google_books(query, max_results=20):
    """Query the Google Books API with a search term or subject safely."""
    url = "https://www.googleapis.com/books/v1/volumes"
    max_results = min(max_results, 40)  # Google API limit
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
    

# RENAMED and FIXED: This now correctly fetches raw API data.
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

def get_nyt_bestsellers(list_name="hardcover-fiction", limit=10):
    """Get NYT bestseller list."""
    # ... (rest of function is fine)
    url = f"https://api.nytimes.com/svc/books/v3/lists/current/{list_name}.json"
    params = {"api-key": getattr(settings, "NYT_BOOKS_API_KEY", None)}
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"NYT API Error: {e}")
        return []
    data = response.json()
    return data.get("results", {}).get("books", [])[:limit]

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
def get_genre_top_books(limit=10):
    """Get top book from each genre (Google Books), with caching."""
    cache_key = "genre_top_books"
    cached_books = cache.get(cache_key)
    if cached_books:
        return cached_books

    genres = ["Science Fiction", "Science", "History", "Biography", "Fantasy", "Romance"]
    books = []
    for genre in genres[:limit]:
        data = search_google_books(f"subject:{genre}", max_results=1)
        if data and "items" in data:
            books.append(normalize_google_book(data["items"][0]))
    
    cache.set(cache_key, books, 60 * 60 * 6)  # Cache for 6 hours
    return books

# ADDED: Caching for performance
def get_recent_books(limit=10):
    """Get recently published books (Google Books), with caching."""
    cache_key = "recent_books"
    cached_books = cache.get(cache_key)
    if cached_books:
        return cached_books
    
    data = search_google_books("newest", max_results=limit)
    if not data:
        return []
    books = [normalize_google_book(item) for item in data.get("items", [])]
    cache.set(cache_key, books, 60 * 60 * 6)  # Cache for 6 hours
    return books

# ADDED: Caching for performance
def get_bestsellers(limit=10):
    """Get bestseller books (NYT), with caching."""
    cache_key = "bestsellers"
    cached_books = cache.get(cache_key)
    if cached_books:
        return cached_books

    books_data = get_nyt_bestsellers(limit=limit)
    books = [normalize_nyt_book(item) for item in books_data]
    cache.set(cache_key, books, 60 * 60 * 6)  # Cache for 6 hours
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
    """Simple pagination utility for list-based data."""
    total = len(items)
    total_pages = ceil(total / page_size)
    start = (page - 1) * page_size
    end = start + page_size
    paginated = items[start:end]

    return {
        "page": page,
        "page_size": page_size,
        "total_items": total,
        "total_pages": total_pages,
        "results": paginated,
    }

# ============================================================
# 🔹 Explore Page Handler (Unified Logic)
# ============================================================

def get_explore_books(query=None, genre=None, sort=None, limit=50, page=1, page_size=10):
    """
    Unified backend handler for the Explore page (search, genre, sorting) with pagination.
    """
    cache_key = f"explore_{query or genre or sort or 'default'}_{limit}"
    cached = cache.get(cache_key)

    if cached:
        books = cached.get("books")
        mode = cached.get("mode", "default")
    else:
        books = []
        mode = "default"

        # Search mode
        if query:
            mode = "search"
            data = search_google_books(query, max_results=limit)
            books = [normalize_google_book(item) for item in data.get("items", [])] if data and "items" in data else []

        # Genre filter
        elif genre:
            mode = "genre"
            data = search_google_books(f"subject:{genre}", max_results=limit)
            books = [normalize_google_book(item) for item in data.get("items", [])] if data and "items" in data else []

        # Sorting
        elif sort == "newest":
            mode = "sorted"
            books = get_recent_books(limit=limit)
        elif sort == "bestsellers":
            mode = "sorted"
            books = get_bestsellers(limit=limit)
        else:
            # Default explore content
            mode = "default"
            books = {
                "carousel": get_genre_top_books(limit=10),
                "recent": get_recent_books(limit=10),
                "bestsellers": get_bestsellers(limit=10),
            }

        cache.set(cache_key, {"mode": mode, "books": books}, timeout=60 * 60 * 3)

    # Paginate only if books is a list
    if isinstance(books, list):
        paginated = paginate_list(books, page=page, page_size=page_size)
    else:
        paginated = {"mode": mode, "sections": books}  # default homepage-style view (no pagination)

    return {"mode": mode, "data": paginated}

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

