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
      className="flex items-center bg-gray-800 border border-gray-700 rounded-xl p-3 hover:scale-[1.02] hover:border-red-500/60 transition cursor-pointer"
    >
      <img
        src={
          book.thumbnail ||
          "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ac/No_image_available.svg/480px-No_image_available.svg.png"
        }
        alt={book.title}
        className="w-16 h-24 rounded-md object-cover"
      />
      <div className="ml-3 flex-1">
        <p className="text-sm font-semibold flex items-center">
          {isBestseller && getRankBadge(book.rank)}
          {book.title}
        </p>
        <p className="text-xs text-gray-400">
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
