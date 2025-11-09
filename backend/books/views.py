import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, generics
from django.shortcuts import get_object_or_404
from django.core.cache import cache
from .models import Book, UserBookInteraction, Review
from .recommender import get_user_recommendations
from django.conf import settings
from django.db.models import Avg
from .tasks import generate_recommendations_task
from .serializers import (
    BookSerializer,
    UserBookInteractionSerializer,
    ReviewSerializer,
    AuthorSerializer,
    
)
from .services import (
    search_google_books,
    normalize_google_book,
    get_or_create_book_details,
    get_genre_top_books,
    get_recent_books,
    get_bestsellers,
    fetch_author_details,
    get_explore_books,
    get_popular_now_books,

)
from .permissions import IsOwnerOrReadOnly
from .tasks import generate_summary_task, generate_book_embedding_task
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import UserBookInteraction, Book
from .serializers import UserBookInteractionSerializer
from rest_framework.parsers import MultiPartParser, FormParser
from .serializers import SummarizeTextSerializer, SummarizeUploadSerializer
from .services import summarize_user_text, summarize_user_upload



# ============================================================
# 🧭 Unified Explore Endpoint (Search + Filter + Sort)
# ============================================================
class ExploreBooksView(APIView):
    """
    Unified Explore endpoint supporting:
      - Full-text search
      - Genre filtering
      - Sorting (newest / popular)
      - Pagination (page, page_size)
      - Caching per combination of params
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        # ---- Query Params ----
        query = request.query_params.get("q")
        genre = request.query_params.get("genre")
        sort = request.query_params.get("sort")
        limit = int(request.query_params.get("limit", 50))
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 10))

        # ---- Cache Key ----
        cache_key = f"explore_{query or genre or sort or 'default'}_{page}_{page_size}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response({**cached_data, "cached": True}, status=status.HTTP_200_OK)

        # ---- Get Explore Data ----
        try:
            result = get_explore_books(
                query=query,
                genre=genre,
                sort=sort,
                limit=limit,
                page=page,
                page_size=page_size,
            )
        except Exception as e:
            # 🔸 Optional fallback: if Google API fails
            fallback = cache.get("explore_fallback")
            if fallback:
                return Response(
                    {
                        "error": str(e),
                        "hint": "Google API failed — showing cached fallback.",
                        "fallback_data": fallback,
                        "cached": True,
                    },
                    status=status.HTTP_502_BAD_GATEWAY,
                )
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # ---- Cache Result ----
        cache.set(cache_key, result, 60 * 60 * 3)  # 3 hours
        cache.set("explore_fallback", result, 60 * 60 * 3)

        # ---- Return Unified Response ----
        return Response({**result, "cached": False}, status=status.HTTP_200_OK)
# -------------------------------
# Book Details
# -------------------------------
class BookDetailView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, google_id):
        book = get_or_create_book_details(google_id)
        if not book:
            return Response({"detail": "Invalid or unavailable Google ID."}, status=status.HTTP_404_NOT_FOUND)

        serializer = BookSerializer(book)
        return Response(serializer.data)



# -------------------------------
# AI Summary (Asynchronous via Celery)
# -------------------------------
class BookSummaryView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, google_id):
        # 1) Ensure the book exists in DB (try quick fetch, else attempt creation)
        book = Book.objects.filter(google_id=google_id).first()
        if not book:
            # attempt to fetch from Google Books and store locally
            book = get_or_create_book_details(google_id)
            if not book:
                # give a helpful error because earlier we returned a confusing "not in DB" message
                return Response({
                    "error": "Book not in database and could not be fetched from Google Books.",
                    "hint": "Ensure GOOGLE_BOOKS_API_KEY is set and Google Books API is reachable. "
                            "First call the book details endpoint (/api/books/<google_id>/) to persist it, "
                            "or check backend logs for fetch errors."
                }, status=status.HTTP_404_NOT_FOUND)

        # 2) If we already have a saved summary, return it immediately
        if book.ai_summary:
            return Response({
                "summary": book.ai_summary,
                "status": "completed",
                "cached": True
            })

        # 3) Check Redis cache (maybe task produced it but didn't persist)
        cache_key = f"book_summary_gemini_{google_id}"
        cached_summary = cache.get(cache_key)
        if cached_summary:
            return Response({
                "summary": cached_summary,
                "status": "completed",
                "cached": True
            })

        # 4) Prevent duplicate tasks: short lock
        task_lock_key = f"book_summary_task_{google_id}"
        if cache.get(task_lock_key):
            return Response({
                "summary": None,
                "status": "processing",
                "message": "Summary generation already in progress."
            })

        # 5) Queue Celery task and return task id to caller
        async_result = generate_summary_task.apply_async(args=[google_id])
        cache.set(task_lock_key, True, timeout=60 * 5)  # 5 min lock

        return Response({
            "summary": None,
            "status": "processing",
            "task_id": async_result.id,
            "message": "Summary generation started. Poll this endpoint or use task_id to track."
        }, status=status.HTTP_202_ACCEPTED)

# -------------------------------
# 🏠 Home / Genre / Recent / Bestseller Books
# -------------------------------
class HomeBooksView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        """
        Unified homepage data — carousel, recent, and popular sections.
        Cached for 1 hour to minimize repeated API calls.
        """
        cache_key = "home_books_combined_v2"
        cached = cache.get(cache_key)

        if cached:
            return Response({**cached, "cached": True}, status=status.HTTP_200_OK)

        # --- Generate fresh data ---
        carousel = get_genre_top_books(limit=10)
        recent = get_recent_books(limit=10)
        popular_now = get_popular_now_books(limit=10)

        result = {
            "carousel": carousel,
            "recent": recent,
            "bestsellers": popular_now,  # kept key same for frontend compatibility
        }

        # --- Cache full response for 1 hour ---
        cache.set(cache_key, result, timeout=60 * 60)

        return Response(result, status=status.HTTP_200_OK)


# -------------------------------
# UserBookInteraction
# -------------------------------
class UserBookInteractionView(APIView):
    """
    POST → Create or update a user-book interaction
    PUT → Explicitly update existing status/favorite flags
    """
    permission_classes = [IsAuthenticated]

    # --- Create or Update (Auto Upsert) ---
    def post(self, request):
        book_id = request.data.get("book")
        status_code = request.data.get("status")
        is_favorite = request.data.get("is_favorite")

        if not book_id:
            return Response({"error": "Book ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Validate status short codes
        valid_statuses = {"WR", "RDG", "RD"}
        if status_code and status_code not in valid_statuses:
            return Response(
                {"error": "Invalid status value. Must be one of WR, RDG, RD."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Ensure book exists
        book = get_object_or_404(Book, google_id=book_id)

        # Create or update user-book interaction
        interaction, created = UserBookInteraction.objects.get_or_create(
            user=request.user, book=book
        )

        if status_code:
            interaction.status = status_code
        if is_favorite is not None:
            interaction.is_favorite = is_favorite

        interaction.save()
        serializer = UserBookInteractionSerializer(interaction)

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    # --- Explicit Update (Existing Interaction Only) ---
    def put(self, request):
        book_id = request.data.get("book_id")
        status_code = request.data.get("status")
        is_favorite = request.data.get("is_favorite")

        if not book_id:
            return Response({"error": "book_id is required."}, status=400)

        try:
            interaction = UserBookInteraction.objects.get(
                user=request.user, book__google_id=book_id
            )
        except UserBookInteraction.DoesNotExist:
            return Response({"error": "Interaction not found."}, status=404)

        # Validate and update fields
        valid_statuses = {"WR", "RDG", "RD"}
        if status_code and status_code not in valid_statuses:
            return Response(
                {"error": "Invalid status value. Must be one of WR, RDG, RD."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if status_code:
            interaction.status = status_code
        if is_favorite is not None:
            interaction.is_favorite = is_favorite

        interaction.save()
        return Response(UserBookInteractionSerializer(interaction).data, status=200)
# -------------------------------
# Review Create / Get for a Book
# -------------------------------
class ReviewListCreateView(APIView):
    """
    GET → Fetch all reviews for a given book.
    POST → Create a new review (or return existing one if already reviewed by user).
    """
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request, book_id):
        book = get_object_or_404(Book, pk=book_id)
        reviews = Review.objects.filter(book=book).select_related("user")
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)

    def post(self, request, book_id):
        book = get_object_or_404(Book, pk=book_id)
        existing_review = Review.objects.filter(user=request.user, book=book).first()

        if existing_review:
            # If review already exists, return it instead of error
            serializer = ReviewSerializer(existing_review)
            return Response(
                {"detail": "You’ve already reviewed this book.", "review": serializer.data},
                status=status.HTTP_200_OK
            )

        serializer = ReviewSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save(user=request.user, book=book)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# -------------------------------
# Review Update
# -------------------------------
class UpdateReviewView(APIView):
    """
    PUT → Update user’s existing review for a given book (by google_id)
    """
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, google_id):
        book = get_object_or_404(Book, google_id=google_id)
        review = get_object_or_404(Review, user=request.user, book=book)

        serializer = ReviewSerializer(review, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# -------------------------------
# Review Delete
# -------------------------------
class DeleteReviewView(APIView):
    """
    DELETE → Remove logged-in user’s review for a given book (by google_id)
    """
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, google_id):
        book = get_object_or_404(Book, google_id=google_id)
        review = get_object_or_404(Review, user=request.user, book=book)

        review.delete()
        return Response({"detail": "Review deleted successfully."}, status=status.HTTP_204_NO_CONTENT)


# -------------------------------
# User Library & Favorites
# -------------------------------
class UserLibraryView(APIView):
    """
    Returns user's library grouped by status:
    {
        "library": {
            "will_read": [...],
            "reading": [...],
            "read": [...],
            "favorites": [...]
        }
    }
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        interactions = (
            UserBookInteraction.objects.filter(user=user)
            .select_related("book")
            .order_by("-id")
        )

        will_read = [i for i in interactions if i.status == UserBookInteraction.Status.WILL_READ]
        reading = [i for i in interactions if i.status == UserBookInteraction.Status.READING]
        read = [i for i in interactions if i.status == UserBookInteraction.Status.READ]
        favorites = [i for i in interactions if i.is_favorite]

        serializer = UserBookInteractionSerializer
        response_data = {
            "library": {
                "will_read": serializer(will_read, many=True).data,
                "reading": serializer(reading, many=True).data,
                "read": serializer(read, many=True).data,
                "favorites": serializer(favorites, many=True).data,
            }
        }

        return Response(response_data, status=status.HTTP_200_OK)

class UserFavoritesView(APIView):
    """
    Returns a flat list of user's favorite books.
    Independent of status (WR / RDG / RD).
    Supports optional ?status= filter.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        status_filter = request.query_params.get("status")

        favorites_qs = UserBookInteraction.objects.filter(
            user=request.user,
            is_favorite=True,
        ).select_related("book")

        if status_filter in [
            UserBookInteraction.Status.WILL_READ,
            UserBookInteraction.Status.READING,
            UserBookInteraction.Status.READ,
        ]:
            favorites_qs = favorites_qs.filter(status=status_filter)

        favorites_qs = favorites_qs.order_by("-id")
        serializer = UserBookInteractionSerializer(favorites_qs, many=True)

        return Response({"favorites": serializer.data}, status=status.HTTP_200_OK)


class RecommendationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        result = get_user_recommendations(request.user, top_n=10)
        if result["status"] == "ready":
            serializer = BookSerializer(result["books"], many=True, context={"request": request})
            return Response({"status": "ready", "recommendations": serializer.data}, status=200)

        # Task trigger (FIXED HERE)
        task = generate_recommendations_task.delay(request.user.id, 10)

        return Response({
            "status": "processing",
            "message": "Recommendation generation started. Retry this endpoint in a few seconds.",
            "task_id": task.id
        }, status=202)

    
    
# ============================================================
# 🔹 Author Endpoints
# ============================================================
class AuthorDetailView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, author_name):
        data = fetch_author_details(author_name)
        serializer = AuthorSerializer(data)
        return Response(serializer.data)


class MoreFromAuthorView(APIView):
    """
    Returns other books from the same author (based on Google Books).
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, author_name):
        data = search_google_books(f"inauthor:{author_name}", max_results=10)
        if not data or "items" not in data:
            return Response({"books": []})
        books = [normalize_google_book(item) for item in data["items"]]
        return Response({"books": books})

class GoogleBooksDebugView(APIView):
    def get(self, request):
        api_key = getattr(settings, "GOOGLE_BOOKS_API_KEY", None)
        query = "harry potter"
        url = "https://www.googleapis.com/books/v1/volumes"
        params = {
            "q": query,
            "maxResults": 5,
            "key": api_key,
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            return Response({
                "used_api_key": api_key,
                "final_url": response.url,
                "status_code": response.status_code,
                "response_excerpt": str(data)[:300],
            })
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
# ============================================================
# 🔹 BOOK DETAIL (FULL)
# ============================================================
class BookDetailFullView(APIView):
    """
    Returns detailed book info including:
    - Full metadata (from DB)
    - AI summary
    - Reviews + avg rating
    - User-specific interaction (if logged in)
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, google_id):
        from .services import get_full_book_details

        result = get_full_book_details(google_id, user=request.user)
        if "error" in result:
            return Response(result, status=status.HTTP_404_NOT_FOUND)
        return Response(result, status=status.HTTP_200_OK)

# books/views.py (add near bottom)
class SummarizeTextView(APIView):
    """
    POST /api/v1/summarize/text/
    Body: { "text": "...", "max_summary_words": 250 }
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = SummarizeTextSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        result = summarize_user_text(
            text=data["text"],
            max_summary_words=data.get("max_summary_words", 250)
        )
        return Response(result, status=status.HTTP_200_OK)


class SummarizeUploadView(APIView):
    """
    POST /api/v1/summarize/upload/
    Form-Data: file=<PDF/DOCX/TXT>, max_summary_words=250
    """
    permission_classes = [permissions.AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = SummarizeUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = summarize_user_upload(
            django_file=serializer.validated_data["file"],
            max_summary_words=serializer.validated_data.get("max_summary_words", 250)
        )
        return Response(result, status=status.HTTP_200_OK)
