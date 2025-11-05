import React from "react";
import { ChevronRight } from "lucide-react";
import BookRowCard from "./BookRowCard";

export default function SectionBlock({
  title,
  data,
  onViewAll,
  isBestseller = false,
}) {
  return (
    <div className="bg-gray-850 rounded-2xl border border-gray-700 p-5 shadow-lg">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-xl font-semibold">{title}</h3>
        <button
          onClick={onViewAll}
          className="flex items-center gap-1 text-sm text-gray-400 hover:text-red-400 transition"
        >
          View all <ChevronRight size={16} />
        </button>
      </div>

      {data.length > 0 ? (
        <div className="flex flex-col gap-3">
          {data.map((book, idx) => (
            <BookRowCard
              key={book.google_id || idx}
              book={book}
              isBestseller={isBestseller}
              onClick={() =>
                isBestseller
                  ? window.open(book.amazon_url, "_blank")
                  : null
              }
            />
          ))}
        </div>
      ) : (
        <p className="text-gray-400 text-center py-8">
          No books available.
        </p>
      )}
    </div>
  );
}
