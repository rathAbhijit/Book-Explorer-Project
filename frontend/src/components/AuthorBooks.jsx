import React, { useRef } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";

export default function AuthorBooks({ books = [], author }) {
  const scrollRef = useRef(null);

  const scroll = (direction) => {
    const container = scrollRef.current;
    if (!container) return;
    const scrollAmount = container.offsetWidth * 0.8;
    container.scrollBy({
      left: direction === "left" ? -scrollAmount : scrollAmount,
      behavior: "smooth",
    });
  };

  if (!books.length)
    return (
      <div className="bg-gray-850 border border-gray-700 rounded-2xl p-6 text-center">
        <p className="text-gray-400">No other books found from this author.</p>
      </div>
    );

  return (
    <div className="relative bg-gray-850 border border-gray-700 rounded-2xl p-6 shadow-lg">
      <h3 className="text-xl font-semibold mb-4 text-red-400">
        More from {author || "this Author"}
      </h3>

      {/* Scroll Buttons */}
      <button
        onClick={() => scroll("left")}
        className="absolute left-3 top-1/2 -translate-y-1/2 bg-black/50 hover:bg-red-600/80 text-white rounded-full p-3 backdrop-blur-sm transition z-10"
      >
        <ChevronLeft size={22} />
      </button>

      <button
        onClick={() => scroll("right")}
        className="absolute right-3 top-1/2 -translate-y-1/2 bg-black/50 hover:bg-red-600/80 text-white rounded-full p-3 backdrop-blur-sm transition z-10"
      >
        <ChevronRight size={22} />
      </button>

      {/* Horizontal Scroll Container */}
      <div
        ref={scrollRef}
        className="flex gap-4 overflow-x-auto scrollbar-hide scroll-smooth pb-3"
      >
        {books.map((book, idx) => (
          <div
            key={book.google_id || idx}
            className="min-w-[170px] max-w-[170px] bg-gray-800 rounded-lg border border-gray-700 flex-shrink-0 hover:scale-[1.03] transition cursor-pointer"
            onClick={() =>
              (window.location.href = `/books/${book.google_id}`)
            }
          >
            <div className="w-full h-56 bg-gray-700 rounded-t-lg overflow-hidden flex justify-center items-center">
              <img
                src={
                  book.thumbnail ||
                  "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ac/No_image_available.svg/480px-No_image_available.svg.png"
                }
                onError={(e) => {
                  e.target.onerror = null;
                  e.target.src =
                    "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ac/No_image_available.svg/480px-No_image_available.svg.png";
                }}
                alt={book.title}
                className="w-full h-full object-cover"
              />
            </div>
            <div className="p-2 h-[75px] overflow-hidden flex flex-col justify-between">
              <p
                className="text-sm font-medium text-gray-100 line-clamp-2"
                title={book.title}
              >
                {book.title}
              </p>
              <p
                className="text-xs text-gray-400 line-clamp-1"
                title={book.authors?.join(", ") || "Unknown Author"}
              >
                {book.authors?.join(", ") || "Unknown Author"}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
