from django.urls import path
from .views import (
    BookDetailView,
    BookSummaryView,
    DeleteReviewView,
    ExploreBooksView,
    GoogleBooksDebugView,
    HomeBooksView,
    UserBookInteractionView,
    UserLibraryView,
    ReviewListCreateView,
    UserFavoritesView,
    BookDetailFullView,
    RecommendationView,
    AuthorDetailView,
    MoreFromAuthorView,
    UpdateReviewView,
    DeleteReviewView,
    SummarizeTextView,
    SummarizeUploadView,
)

urlpatterns = [
    path("explore/", ExploreBooksView.as_view(), name="explore-books"),
    path("details/<str:google_id>/", BookDetailView.as_view(), name="book-detail"),
    path("details-full/<str:google_id>/", BookDetailFullView.as_view(), name="book-detail-full"),
    path("summary/<str:google_id>/", BookSummaryView.as_view(), name="book-summary"),
    path("home/", HomeBooksView.as_view(), name="home-books"),
    
    # Interaction & Library URLs
    path("interactions/", UserBookInteractionView.as_view(), name="user-interaction"),
    path("my-library/", UserLibraryView.as_view(), name="user-library"),
    path("favorites/", UserFavoritesView.as_view(), name="user-favorites"),
    
    # Review URLs
    # FIXED: The URL parameter now correctly uses 'book_id' to match the view.
    path("create-review/<str:book_id>/", ReviewListCreateView.as_view(), name="review-create"),
    path("update-review/<str:google_id>/", UpdateReviewView.as_view(), name="update-review"),
    path("delete-review/<str:google_id>/", DeleteReviewView.as_view(), name="delete-review"),
    path("recommendations/", RecommendationView.as_view(), name="recommendations"),


    # Author-related endpoints
    path("author/<str:author_name>/", AuthorDetailView.as_view(), name="author-detail"),
    path("books/more-from-author/<str:author_name>/", MoreFromAuthorView.as_view(), name="more-from-author"),

    path("summarize/text/", SummarizeTextView.as_view(), name="summarize-text"),
    path("summarize/upload/", SummarizeUploadView.as_view(), name="summarize-upload"),


    path("debug/google-books/", GoogleBooksDebugView.as_view()),
]