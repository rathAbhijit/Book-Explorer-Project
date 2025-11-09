import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import toast from "react-hot-toast";
import {
  getBookDetail,
  getBookDetailFull,
  getSummary,
  createReview,
  updateReview,
  deleteReview,
  setInteraction,
  getMoreFromAuthor,
} from "../services/bookApi";
import { useAuth } from "../context/AuthContext";
import BookInfoCard from "../components/BookInfoCard";
import ReviewSection from "../components/ReviewSection";
import SummaryCard from "../components/SummaryCard";
import AuthorBooks from "../components/AuthorBooks";
import Skeleton from "../components/Skeleton";

export default function BookDetails() {
  const { google_id } = useParams();
  const { user } = useAuth();

  // Core Data States
  const [book, setBook] = useState(null);
  const [reviews, setReviews] = useState([]);
  const [userInteraction, setUserInteraction] = useState(null);
  const [summary, setSummary] = useState(null);
  const [authorBooks, setAuthorBooks] = useState([]);

  // Loading States
  const [loadingBook, setLoadingBook] = useState(true);
  const [loadingSummary, setLoadingSummary] = useState(true);
  const [loadingReviews, setLoadingReviews] = useState(true);
  const [loadingAuthor, setLoadingAuthor] = useState(true);

  useEffect(() => {
    fetchBookDetails();
  }, [google_id]);

  // ----------------------------
  // Load main book info first
  // ----------------------------
  const fetchBookDetails = async () => {
    setLoadingBook(true);
    try {
      // 🔹 Step 1: Trigger database creation
      await getBookDetail(google_id);

      // 🔹 Step 2: Fetch full book details
      const { data } = await getBookDetailFull(google_id);

      setBook(data.book);
      setReviews(data.reviews || []);
      setUserInteraction(data.user_interaction || {});

      setLoadingBook(false);

      // Load related data in parallel
      if (data.book?.authors?.length) {
        fetchAuthorBooks(data.book.authors[0]);
      }
      fetchSummary(google_id);
    } catch (err) {
      console.error("BOOK DETAILS ERROR:", err);
      toast.error("Failed to load book details");
      setLoadingBook(false);
    } finally {
      setLoadingReviews(false); // reviews come with book data
    }
  };

  // ----------------------------
  // Load AI Summary separately
  // ----------------------------
  const fetchSummary = async (id) => {
    try {
      const { data } = await getSummary(id);
      if (data.status === "processing") {
        setSummary(null);
      } else {
        setSummary(data.summary);
      }
    } catch {
      setSummary(null);
    } finally {
      setLoadingSummary(false);
    }
  };

  // ----------------------------
  // Load More From Author
  // ----------------------------
  const fetchAuthorBooks = async (author) => {
    setLoadingAuthor(true);
    try {
      const { data } = await getMoreFromAuthor(author);
      setAuthorBooks(data.books || []);
    } catch {
      setAuthorBooks([]);
    } finally {
      setLoadingAuthor(false);
    }
  };

  // ----------------------------
  // User Interactions
  // ----------------------------
  const handleInteraction = async (status, isFavorite) => {
    try {
      await setInteraction({ book: google_id, status, is_favorite: isFavorite });
      toast.success("Interaction updated");
      fetchBookDetails();
    } catch {
      toast.error("Could not update interaction");
    }
  };

  const handleReview = async (payload, mode) => {
    try {
      if (mode === "create") await createReview(google_id, payload);
      else if (mode === "update") await updateReview(google_id, payload);
      else if (mode === "delete") await deleteReview(google_id);

      toast.success("Review updated");
      fetchBookDetails();
    } catch {
      toast.error("Failed to modify review");
    }
  };

  // ----------------------------
  // Rendering
  // ----------------------------
  return (
    <div className="min-h-screen bg-gray-900 text-white p-6 flex flex-col items-center">
      <div className="w-full max-w-5xl flex flex-col gap-8">

        {/* Book Info Section */}
        {loadingBook ? (
          <div className="flex flex-col md:flex-row gap-6 bg-gray-850 border border-gray-700 rounded-2xl p-6 shadow-lg animate-pulse">
            <Skeleton className="w-48 h-72" />
            <div className="flex-1 flex flex-col gap-3">
              <Skeleton className="h-6 w-1/2" />
              <Skeleton className="h-4 w-1/3" />
              <Skeleton className="h-3 w-full" />
              <Skeleton className="h-3 w-5/6" />
              <Skeleton className="h-3 w-4/6" />
            </div>
          </div>
        ) : (
          <BookInfoCard
            book={book}
            userInteraction={userInteraction}
            onInteraction={handleInteraction}
          />
        )}

        {/* AI Summary Section */}
        {loadingSummary ? (
          <div className="bg-gray-850 border border-gray-700 rounded-2xl p-6 animate-pulse">
            <Skeleton className="h-5 w-32 mb-3" />
            <Skeleton className="h-4 w-full mb-2" />
            <Skeleton className="h-4 w-5/6" />
          </div>
        ) : (
          <SummaryCard
            summary={summary}
            onGenerate={() => fetchSummary(google_id)}
          />
        )}

        {/* Reviews Section */}
        {loadingReviews ? (
          <div className="bg-gray-850 border border-gray-700 rounded-2xl p-6 animate-pulse">
            <Skeleton className="h-5 w-32 mb-3" />
            {[1, 2, 3].map((i) => (
              <div key={i} className="mt-3">
                <Skeleton className="h-3 w-1/3 mb-2" />
                <Skeleton className="h-3 w-3/4" />
              </div>
            ))}
          </div>
        ) : (
          <ReviewSection
            reviews={reviews}
            user={user}
            onReviewAction={handleReview}
          />
        )}

        {/* Author Books Section */}
        {loadingAuthor ? (
          <div className="bg-gray-850 border border-gray-700 rounded-2xl p-6 animate-pulse">
            <Skeleton className="h-5 w-1/4 mb-4" />
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[1, 2, 3, 4].map((i) => (
                <Skeleton key={i} className="h-40 w-full rounded-md" />
              ))}
            </div>
          </div>
        ) : (
          <AuthorBooks books={authorBooks} author={book?.authors?.[0]} />
        )}
      </div>
    </div>
  );
}
