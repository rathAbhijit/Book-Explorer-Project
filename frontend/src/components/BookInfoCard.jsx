import React, { useState } from "react";
import { Heart, BookOpen, BookmarkCheck, Clock } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { useNavigate } from "react-router-dom";

export default function BookInfoCard({ book, userInteraction, onInteraction }) {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [showFullDesc, setShowFullDesc] = useState(false);

  if (!book) return null;

  const handleFavoriteToggle = () => {
    onInteraction({
      book: book.google_id,
      status: userInteraction?.status || "WR",
      is_favorite: !userInteraction?.is_favorite,
    });
  };

  const handleStatusChange = (newStatus) => {
    onInteraction({
      book: book.google_id,
      status: newStatus,
      is_favorite: userInteraction?.is_favorite || false,
    });
  };

  const currentStatus = userInteraction?.status;
  const rating =
    book.average_rating !== null && book.average_rating !== undefined
      ? book.average_rating.toFixed(1)
      : null;

  return (
    <div className="flex flex-col md:flex-row gap-6 bg-gray-850 border border-gray-700 rounded-2xl p-6 shadow-lg transition-all">
      {/* Fixed Thumbnail */}
      <div className="flex-shrink-0 w-full md:w-1/3 flex justify-center items-start">
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
          className="rounded-lg w-52 h-72 object-cover shadow-lg border border-gray-700 sticky top-24"
        />
      </div>

      {/* Book Details */}
      <div className="flex-1 flex flex-col justify-between">
        {/* Title & Author */}
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

          {/* Description Section */}
          <div className="relative">
            <div
              className={`text-gray-300 text-sm leading-relaxed transition-all duration-300 ${
                showFullDesc ? "" : "line-clamp-[8] overflow-hidden"
              }`}
              dangerouslySetInnerHTML={{
                __html:
                  book.short_description ||
                  book.description ||
                  "No description available.",
              }}
            />
            {(book.description || book.short_description) && (
              <button
                onClick={() => setShowFullDesc(!showFullDesc)}
                className="text-red-400 mt-2 text-sm hover:underline"
              >
                {showFullDesc ? "Show Less ▲" : "Show More ▼"}
              </button>
            )}
          </div>
        </div>

        {/* Interaction Buttons */}
        {isAuthenticated && (
          <div className="flex flex-wrap items-center gap-3 mt-5">
            {/* Status Buttons */}
            <button
              onClick={() => handleStatusChange("WR")}
              className={`flex items-center gap-2 px-3 py-2 rounded-md text-xs font-medium border ${
                currentStatus === "WR"
                  ? "bg-yellow-600 border-yellow-500 text-white"
                  : "bg-gray-800 border-gray-700 text-gray-300 hover:border-yellow-400"
              }`}
            >
              <Clock size={14} />
              Will Read
            </button>

            <button
              onClick={() => handleStatusChange("RDG")}
              className={`flex items-center gap-2 px-3 py-2 rounded-md text-xs font-medium border ${
                currentStatus === "RDG"
                  ? "bg-blue-600 border-blue-500 text-white"
                  : "bg-gray-800 border-gray-700 text-gray-300 hover:border-blue-400"
              }`}
            >
              <BookOpen size={14} />
              Reading
            </button>

            <button
              onClick={() => handleStatusChange("RD")}
              className={`flex items-center gap-2 px-3 py-2 rounded-md text-xs font-medium border ${
                currentStatus === "RD"
                  ? "bg-green-600 border-green-500 text-white"
                  : "bg-gray-800 border-gray-700 text-gray-300 hover:border-green-400"
              }`}
            >
              <BookmarkCheck size={14} />
              Read
            </button>

            {/* Favorite Toggle */}
            <button
              onClick={handleFavoriteToggle}
              className={`flex items-center gap-2 px-3 py-2 rounded-md text-xs font-medium border ${
                userInteraction?.is_favorite
                  ? "bg-red-600 border-red-500 text-white"
                  : "bg-gray-800 border-gray-700 text-gray-300 hover:border-red-400"
              }`}
            >
              <Heart
                size={14}
                className={userInteraction?.is_favorite ? "fill-current" : ""}
              />
              {userInteraction?.is_favorite ? "Favorited" : "Favorite"}
            </button>

            {/* Rating */}
            {rating ? (
              <p className="text-yellow-400 text-sm">⭐ {rating}/5</p>
            ) : (
              <p className="text-gray-500 text-sm">⭐ No ratings</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
