from backend.books.models import UserBookInteraction, Review
from django.db.models import Count

def get_user_dashboard_data(user):
    """
    Gather key statistics and recent activities for a user's dashboard.
    """
    # --- Book stats ---
    stats = {
        "total_books": UserBookInteraction.objects.filter(user=user).count(),
        "books_read": UserBookInteraction.objects.filter(user=user, status="RD").count(),
        "books_reading": UserBookInteraction.objects.filter(user=user, status="RDG").count(),
        "books_want_to_read": UserBookInteraction.objects.filter(user=user, status="WTR").count(),
        "favorites": UserBookInteraction.objects.filter(user=user, is_favorite=True).count(),
        "total_reviews": Review.objects.filter(user=user).count(),
    }

    # --- Recent activity (latest 5 interactions) ---
    recent_interactions = (
        UserBookInteraction.objects.filter(user=user)
        .select_related("book")
        .order_by("-id")[:5]
    )

    # --- Recent reviews (latest 5) ---
    recent_reviews = (
        Review.objects.filter(user=user)
        .select_related("book")
        .order_by("-created_at")[:5]
    )

    return {
        "stats": stats,
        "recent_interactions": recent_interactions,
        "recent_reviews": recent_reviews,
    }
