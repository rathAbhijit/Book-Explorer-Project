import React, { useState } from "react";
import { Heart, BookmarkCheck } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { useNavigate } from "react-router-dom";

// Helper to decode HTML entities
function decodeHTML(str) {
  if (!str) return "";
  const txt = document.createElement("textarea");
  txt.innerHTML = str;
  return txt.value;
}

export default function BookInfoCard({ book, userInteraction, onInteraction }) {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [expanded, setExpanded] = useState(false);

  if (!book) return null;

  const handleFavorite = () => {
    onInteraction(userInteraction?.status || "RDG", !userInteraction?.is_favorite);
  };

  const handleMarkAsRead = () => {
    onInteraction("RD", userInteraction?.is_favorite || false);
  };

  const rating =
    book.average_rating !== null && book.average_rating !== undefined
      ? book.average_rating.toFixed(1)
      : null;

  // Decode HTML safely
  const decodedDescription = decodeHTML(
    book.short_description ||
      book.description ||
      "No description available for this book."
  );

  // Shorten long descriptions
  const maxLength = 350;
  const showToggle = decodedDescription.length > maxLength;
  const displayDescription = expanded
    ? decodedDescription
    : decodedDescription.slice(0, maxLength) + (showToggle ? "..." : "");

  return (
    <div className="flex flex-col md:flex-row gap-6 bg-gray-850 border border-gray-700 rounded-2xl p-6 shadow-lg">
      {/* Book Cover */}
      <div className="flex-shrink-0 w-full md:w-1/3 flex justify-center items-center">
        <img
          src={
            book.thumbnail_url ||
            book.thumbnail ||
            "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ac/No_image_available.svg/480px-No_image_available.svg.png"
          }
          alt={book.title}
          onError={(e) => {
            e.target.onerror = null;
            e.target.src =
              "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ac/No_image_available.svg/480px-No_image_available.svg.png";
          }}
          className="rounded-lg w-52 h-72 object-cover shadow-lg border border-gray-700"
        />
      </div>

      {/* Book Details */}
      <div className="flex-1 flex flex-col justify-between">
        <div>
          <h2 className="text-2xl font-bold text-red-400 mb-2">{book.title}</h2>

          {book.authors?.length ? (
            <p
              className="text-lg text-gray-300 font-medium mb-3 hover:text-red-400 transition cursor-pointer"
              onClick={() =>
                navigate(`/author/${encodeURIComponent(book.authors[0])}`)
              }
            >
              {book.authors.join(", ")}
            </p>
          ) : (
            <p className="text-gray-500 mb-3">Unknown Author</p>
          )}

          <p
            className="text-gray-300 text-sm leading-relaxed"
            dangerouslySetInnerHTML={{ __html: displayDescription }}
          ></p>

          {showToggle && (
            <button
              onClick={() => setExpanded((prev) => !prev)}
              className="mt-2 text-sm text-red-400 hover:underline"
            >
              {expanded ? "Show less" : "Show more"}
            </button>
          )}
        </div>

        {/* Interaction Buttons (only visible if logged in) */}
        {isAuthenticated && (
          <div className="flex items-center gap-3 mt-5">
            <button
              onClick={handleFavorite}
              className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition border ${
                userInteraction?.is_favorite
                  ? "bg-red-600 text-white border-red-500 hover:bg-red-700"
                  : "bg-gray-800 text-gray-300 border-gray-600 hover:border-red-400"
              }`}
            >
              <Heart
                size={16}
                className={userInteraction?.is_favorite ? "fill-current" : ""}
              />
              {userInteraction?.is_favorite ? "Favorited" : "Favorite"}
            </button>

            <button
              onClick={handleMarkAsRead}
              className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition border ${
                userInteraction?.status === "RD"
                  ? "bg-green-600 text-white border-green-500 hover:bg-green-700"
                  : "bg-gray-800 text-gray-300 border-gray-600 hover:border-green-400"
              }`}
            >
              <BookmarkCheck
                size={16}
                className={
                  userInteraction?.status === "RD" ? "fill-current" : ""
                }
              />
              {userInteraction?.status === "RD" ? "Read" : "Mark as Read"}
            </button>

            {rating ? (
              <p className="text-yellow-400 flex items-center text-sm">
                ⭐ {rating}/5
              </p>
            ) : (
              <p className="text-gray-500 text-sm">⭐ No ratings</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
