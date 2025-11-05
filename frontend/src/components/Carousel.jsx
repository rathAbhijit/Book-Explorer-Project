import React, { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { useNavigate } from "react-router-dom";

export default function Carousel({ items = [] }) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const navigate = useNavigate();

  useEffect(() => {
    if (!items.length) return;
    const interval = setInterval(() => {
      setCurrentIndex((prev) => (prev === items.length - 1 ? 0 : prev + 1));
    }, 6000);
    return () => clearInterval(interval);
  }, [items]);

  if (!items.length)
    return (
      <div className="w-full h-80 bg-gray-800 flex justify-center items-center rounded-2xl border border-gray-700">
        <p className="text-gray-400">No featured books available.</p>
      </div>
    );

  const current = items[currentIndex];

  return (
    <div className="relative overflow-hidden rounded-2xl shadow-lg border border-gray-700 h-80 bg-gray-850 flex">
      <AnimatePresence mode="wait">
        <motion.div
          key={current.google_id}
          initial={{ opacity: 0, x: 60 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -60 }}
          transition={{ duration: 0.6, ease: "easeInOut" }}
          className="absolute inset-0 flex"
        >
          {/* Left: Book Cover */}
          <div className="w-1/3 h-full flex justify-center items-center p-4">
            <img
              src={
                current.thumbnail ||
                "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ac/No_image_available.svg/480px-No_image_available.svg.png"
              }
              alt={current.title}
              className="rounded-lg h-64 w-auto object-cover shadow-lg border border-gray-700 hover:scale-105 transition"
            />
          </div>

          {/* Right: Details */}
          <div className="w-2/3 flex flex-col justify-center pr-10 pl-4">
            <h2 className="text-3xl font-bold text-red-400 mb-2">
              {current.title}
            </h2>
            <p className="text-gray-400 mb-3 text-sm">
              {current.authors?.join(", ") || "Unknown Author"}
            </p>
            <p className="text-gray-200 text-sm leading-relaxed line-clamp-4">
              {current.description || "No description available for this book."}
            </p>
            <button
              onClick={() => navigate(`/books/${current.google_id}`)}
              className="mt-5 px-5 py-2 bg-red-600 hover:bg-red-700 rounded-lg text-sm font-medium w-fit"
            >
              View Details
            </button>
          </div>
        </motion.div>
      </AnimatePresence>

      {/* Nav Arrows */}
      <button
        onClick={() =>
          setCurrentIndex((prev) =>
            prev === 0 ? items.length - 1 : prev - 1
          )
        }
        className="absolute left-4 top-1/2 -translate-y-1/2 bg-black/40 hover:bg-red-500/70 text-white rounded-full p-3 backdrop-blur-sm transition"
      >
        <ChevronLeft size={22} />
      </button>

      <button
        onClick={() =>
          setCurrentIndex((prev) =>
            prev === items.length - 1 ? 0 : prev + 1
          )
        }
        className="absolute right-4 top-1/2 -translate-y-1/2 bg-black/40 hover:bg-red-500/70 text-white rounded-full p-3 backdrop-blur-sm transition"
      >
        <ChevronRight size={22} />
      </button>

      {/* Dots */}
      <div className="absolute bottom-3 left-1/2 -translate-x-1/2 flex gap-2">
        {items.map((_, i) => (
          <button
            key={i}
            onClick={() => setCurrentIndex(i)}
            className={`w-3 h-3 rounded-full transition ${
              i === currentIndex
                ? "bg-red-500 scale-110"
                : "bg-gray-400/70 hover:bg-gray-300"
            }`}
          />
        ))}
      </div>
    </div>
  );
}
