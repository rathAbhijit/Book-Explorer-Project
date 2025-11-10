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
  updateInteraction,
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

  /* =====================================================
     🔹 Fetch Main Book Details
  ===================================================== */
  const fetchBookDetails = async () => {
    setLoadingBook(true);
    try {
      // Step 1: Ensure book is stored in DB
      await getBookDetail(google_id);

      // Step 2: Fetch complete book details
      const { data } = await getBookDetailFull(google_id);

      setBook(data.book);
      setReviews(data.reviews || []);
      setUserInteraction(data.user_interaction || null);

      setLoadingBook(false);

      // Step 3: Load related data
      if (data.book?.authors?.length) fetchAuthorBooks(data.book.authors[0]);
      fetchSummary(google_id);
    } catch (err) {
      console.error("BOOK DETAILS ERROR:", err);
      toast.error("Failed to load book details");
      setLoadingBook(false);
    } finally {
      setLoadingReviews(false);
    }
  };

  /* =====================================================
     🔹 Fetch AI Summary
  ===================================================== */
  const fetchSummary = async (id) => {
    try {
      const { data } = await getSummary(id);
      setSummary(data.status === "processing" ? null : data.summary);
    } catch {
      setSummary(null);
    } finally {
      setLoadingSummary(false);
    }
  };

  /* =====================================================
     🔹 Fetch More Books From Author
  ===================================================== */
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

  /* =====================================================
     🔹 Handle Interaction (Status + Favorite)
  ===================================================== */
  const handleInteraction = async (payload) => {
    try {
      // If user already has interaction → update via PUT
      if (userInteraction && userInteraction.status) {
        const { data } = await updateInteraction({
          book_id: google_id,
          status: payload.status,
          is_favorite: payload.is_favorite,
        });
        setUserInteraction(data);
        toast.success("Interaction updated");
      } else {
        // Otherwise → create new via POST
        const { data } = await setInteraction({
          book: google_id,
          status: payload.status || "WR",
          is_favorite: payload.is_favorite || false,
        });
        setUserInteraction(data);
        toast.success("Added to your library");
      }
    } catch (error) {
      console.error("Interaction error:", error);
      toast.error("Failed to update interaction");
    }
  };

  /* =====================================================
     🔹 Handle Review Actions (Create / Update / Delete)
  ===================================================== */
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

  /* =====================================================
     🔹 Rendering
  ===================================================== */
  return (
    <div className="min-h-screen bg-gray-900 text-white p-6 flex flex-col items-center">
      <div className="w-full max-w-5xl flex flex-col gap-8">
        {/* 📘 Book Info */}
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

        {/* 🧠 AI Summary */}
        {loadingSummary ? (
          <div className="bg-gray-850 border border-gray-700 rounded-2xl p-6 animate-pulse">
            <Skeleton className="h-5 w-32 mb-3" />
            <Skeleton className="h-4 w-full mb-2" />
            <Skeleton className="h-4 w-5/6" />
          </div>
        ) : (
          <SummaryCard summary={summary} onGenerate={() => fetchSummary(google_id)} />
        )}

        {/* 💬 Reviews */}
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
          <ReviewSection reviews={reviews} user={user} onReviewAction={handleReview} />
        )}

        {/* ✍️ Author Books */}
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
