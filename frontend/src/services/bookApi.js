import API from "./api";

// -------------------------
// 🔹 HOME DATA
// -------------------------
export const getHomeData = () => API.get("home/");

// -------------------------
// 🔹 BOOKS
// -------------------------
export const exploreBooks = (q, maxResults = 20) =>
  API.get(`explore/`, { params: { q, maxResults } });

export const getBookDetail = (googleId) => API.get(`details/${googleId}/`);
export const getBookDetailFull = (googleId) => API.get(`details-full/${googleId}/`);
export const getSummary = (googleId) => API.get(`summary/${googleId}/`);

// -------------------------
// 🔹 REVIEWS
// -------------------------
export const createReview = (googleId, payload) =>
  API.post(`create-review/${googleId}/`, payload);

export const updateReview = (googleId, payload) =>
  API.patch(`update-review/${googleId}/`, payload);

export const deleteReview = (googleId) =>
  API.delete(`delete-review/${googleId}/`);

// -------------------------
// 🔹 LIBRARY
// -------------------------
export const setInteraction = (payload) =>
  API.post(`interactions/`, payload); // { book, status, is_favorite }

export const getMyLibrary = () => API.get(`my-library/`);
export const getFavorites = () => API.get(`favorites/`);

// -------------------------
// 🔹 RECOMMENDATIONS
// -------------------------
export const getRecommendations = () => API.get(`recommendations/`);

// -------------------------
// 🔹 AUTHORS
// -------------------------
export const getAuthorDetails = (authorName) =>
  API.get(`author/${encodeURIComponent(authorName)}/`);

export const getMoreFromAuthor = (authorName) =>
  API.get(`books/more-from-author/${encodeURIComponent(authorName)}/`);
