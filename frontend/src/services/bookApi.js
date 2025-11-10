import API from "./api";

/* =====================================================
   🔹 HOME DATA
===================================================== */
export const getHomeData = () => API.get("home/");

/* =====================================================
   🔹 EXPLORE
===================================================== */
export const getExploreData = (params = {}) => API.get("explore/", { params });

/* =====================================================
   🔹 BOOK DETAILS + SUMMARY
===================================================== */
// Basic details
export const getBookDetail = (googleId) => API.get(`details/${googleId}/`);

// Full details (with extended info, author, categories, etc.)
export const getBookDetailFull = (googleId) =>
  API.get(`details-full/${googleId}/`);

// AI-powered spoiler-free summary (cached)
export const getSummary = (googleId) => API.get(`summary/${googleId}/`);

/* =====================================================
   🔹 REVIEWS (CRUD)
===================================================== */
export const createReview = (googleId, payload) =>
  API.post(`create-review/${googleId}/`, payload);

export const updateReview = (googleId, payload) =>
  API.patch(`update-review/${googleId}/`, payload);

export const deleteReview = (googleId) =>
  API.delete(`delete-review/${googleId}/`);

/* =====================================================
   🔹 USER INTERACTIONS (Library + Favorites System v2)
===================================================== */

// Create a new interaction
// Required: { book: "google_id", status?, is_favorite? }
export const createInteraction = (payload) => API.post("interactions/", payload);

// Update an existing interaction
// Required: { book_id: "google_id", status?, is_favorite? }
export const updateInteraction = (payload) => API.put("interactions/", payload);

// Unified handler — automatically decides between POST and PUT
export const setInteraction = (payload) => {
  if (payload.book_id) {
    return updateInteraction(payload);
  } else if (payload.book) {
    return createInteraction(payload);
  } else {
    throw new Error("Missing book or book_id field in payload for interaction");
  }
};

// Get all user-book interactions grouped by reading status + favorites
export const getMyLibrary = () => API.get("my-library/");

// Get all favorite books (optional ?status=WR|RDG|RD)
export const getFavorites = (status) =>
  API.get(status ? `favorites/?status=${status}` : "favorites/");

/* =====================================================
   🔹 RECOMMENDATIONS (async Celery-based)
===================================================== */
export const getRecommendations = () => API.get("recommendations/");

/* =====================================================
   🔹 AUTHORS
===================================================== */
// Get author details
export const getAuthorDetails = (authorName) =>
  API.get(`author/${encodeURIComponent(authorName)}/`);

// Get more books by the same author
export const getMoreFromAuthor = (authorName) =>
  API.get(`books/more-from-author/${encodeURIComponent(authorName)}/`);

/* =====================================================
   🔹 SUMMARIZER ENDPOINTS (for uploads & raw text)
===================================================== */
// Summarize raw text
export const summarizeText = (text, maxWords = 250) =>
  API.post("summarize/text/", { text, max_summary_words: maxWords });

// Summarize uploaded document (PDF, DOCX, TXT)
export const summarizeFile = (file, maxWords = 250) => {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("max_summary_words", maxWords);
  return API.post("summarize/upload/", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
};
