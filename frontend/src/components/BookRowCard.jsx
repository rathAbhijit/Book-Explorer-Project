import React from "react";

export default function BookRowCard({ book, isBestseller = false, onClick }) {
  const getRankBadge = (rank) => {
    if (!rank) return null;
    const colors = {
      1: "bg-yellow-500 text-black",
      2: "bg-gray-300 text-black",
      3: "bg-amber-700 text-white",
    };
    const emoji = { 1: "🥇", 2: "🥈", 3: "🥉" }[rank];
    const cls =
      colors[rank] ||
      "bg-gray-700 text-gray-200 border border-gray-600 text-xs px-1 rounded";
    return (
      <span
        className={`inline-flex items-center text-xs font-bold px-2 py-1 rounded-md ${cls} mr-2`}
      >
        {emoji || `#${rank}`}
      </span>
    );
  };

  return (
    <div
      onClick={onClick}
      className="flex flex-col sm:flex-row items-center sm:items-start bg-gray-800 border border-gray-700 rounded-xl p-4 hover:scale-[1.02] hover:border-red-500/60 transition cursor-pointer w-full h-auto sm:h-36 overflow-hidden"
    >
      {/* Book Thumbnail */}
      <div className="flex-shrink-0 mb-3 sm:mb-0 sm:mr-4">
        <img
          src={
            book.thumbnail ||
            "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ac/No_image_available.svg/480px-No_image_available.svg.png"
          }
          alt={book.title}
          className="w-20 h-28 object-cover rounded-md border border-gray-700 mx-auto sm:mx-0"
          onError={(e) => {
            e.currentTarget.src =
              "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ac/No_image_available.svg/480px-No_image_available.svg.png";
          }}
        />
      </div>

      {/* Book Info */}
      <div className="flex-1 min-w-0 text-center sm:text-left">
        <p className="text-sm font-semibold flex justify-center sm:justify-start items-center text-white line-clamp-1">
          {isBestseller && getRankBadge(book.rank)}
          {book.title}
        </p>

        <p className="text-xs text-gray-400 truncate">
          {book.authors?.length ? book.authors.join(", ") : "Unknown Author"}
        </p>

        {book.description && (
          <p className="text-xs text-gray-500 mt-1 line-clamp-2">
            {book.description}
          </p>
        )}
      </div>
    </div>
  );
}
