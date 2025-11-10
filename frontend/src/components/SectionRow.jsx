import React, { useRef } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { useNavigate } from "react-router-dom";

export default function SectionRow({ category, books, onViewAll }) {
  const scrollRef = useRef(null);
  const navigate = useNavigate();

  const scrollContainer = (dir) => {
    if (!scrollRef.current) return;
    const scrollAmount = 600;
    scrollRef.current.scrollBy({
      left: dir === "left" ? -scrollAmount : scrollAmount,
      behavior: "smooth",
    });
  };

  if (!books.length) return null;

  return (
    <div className="relative group">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-xl font-semibold capitalize">
          {category.replace(/_/g, " ")}
        </h3>
        <button
          onClick={onViewAll}
          className="text-sm text-gray-400 hover:text-red-400 transition"
        >
          View all →
        </button>
      </div>

      <div
        ref={scrollRef}
        className="flex overflow-x-auto scrollbar-hide scroll-smooth gap-4 pb-2"
      >
        {books.map((book) => (
          <div
            key={book.google_id}
            onClick={() => navigate(`/books/${book.google_id}`)}
            className="flex-shrink-0 w-44 bg-gray-850 border border-gray-700 rounded-xl p-3 hover:border-red-500/60 transition cursor-pointer"
          >
            <img
              src={
                book.thumbnail ||
                "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ac/No_image_available.svg/480px-No_image_available.svg.png"
              }
              alt={book.title}
              className="w-full h-60 object-cover rounded-md mb-2"
              onError={(e) =>
                (e.currentTarget.src =
                  "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ac/No_image_available.svg/480px-No_image_available.svg.png")
              }
            />
            <h4 className="text-sm font-semibold line-clamp-2">
              {book.title}
            </h4>
            <p className="text-xs text-gray-400 line-clamp-1">
              {book.authors?.join(", ") || "Unknown Author"}
            </p>
          </div>
        ))}
      </div>

      {/* Scroll Arrows */}
      <button
        onClick={() => scrollContainer("left")}
        className="absolute left-0 top-1/2 -translate-y-1/2 bg-black/40 hover:bg-red-500/70 p-2 rounded-full transition hidden sm:group-hover:block"
      >
        <ChevronLeft size={22} />
      </button>
      <button
        onClick={() => scrollContainer("right")}
        className="absolute right-0 top-1/2 -translate-y-1/2 bg-black/40 hover:bg-red-500/70 p-2 rounded-full transition hidden sm:group-hover:block"
      >
        <ChevronRight size={22} />
      </button>
    </div>
  );
}
