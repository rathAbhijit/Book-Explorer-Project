// src/pages/Library.jsx
import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getMyLibrary } from "../services/bookApi";
import { useAuth } from "../context/AuthContext";
import toast from "react-hot-toast";
import Skeleton from "../components/Skeleton";

export default function Library() {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [library, setLibrary] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (isAuthenticated) fetchLibrary();
  }, [isAuthenticated]);

  const fetchLibrary = async () => {
    try {
      setLoading(true);
      const { data } = await getMyLibrary();
      setLibrary(data.library);
    } catch (err) {
      console.error(err);
      toast.error("Failed to load your library");
    } finally {
      setLoading(false);
    }
  };

  const handleBookClick = (googleId) => {
    navigate(`/books/${googleId}`);
  };

  if (!isAuthenticated)
    return (
      <div className="text-center text-gray-400 mt-10">
        Please log in to view your library.
      </div>
    );

  if (loading)
    return (
      <div className="p-6 space-y-6">
        {[1, 2, 3].map((i) => (
          <div key={i} className="bg-gray-850 p-6 rounded-xl animate-pulse">
            <Skeleton className="h-5 w-1/4 mb-4" />
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[1, 2, 3, 4].map((j) => (
                <Skeleton key={j} className="h-40 w-full rounded-md" />
              ))}
            </div>
          </div>
        ))}
      </div>
    );

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      <div className="max-w-6xl mx-auto space-y-10">
        {["will_read", "reading", "read", "favorites"].map((section) => {
          const books = library?.[section] || [];
          if (!books.length) return null;

          const sectionTitle = {
            will_read: "📘 Will Read",
            reading: "📖 Reading",
            read: "✅ Read",
            favorites: "❤️ Favorites",
          }[section];

          return (
            <div
              key={section}
              className="bg-gray-850 border border-gray-700 rounded-2xl p-6 shadow-md"
            >
              <h2 className="text-xl font-semibold text-red-400 mb-4">
                {sectionTitle}
              </h2>

              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-5">
                {books.map((item) => (
                  <div
                    key={item.book.google_id}
                    onClick={() => handleBookClick(item.book.google_id)}
                    className="cursor-pointer bg-gray-800 hover:bg-gray-750 border border-gray-700 rounded-xl p-3 transition hover:scale-[1.03]"
                  >
                    <img
                      src={
                        item.book.thumbnail_url ||
                        item.book.thumbnail ||
                        "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ac/No_image_available.svg/480px-No_image_available.svg.png"
                      }
                      alt={item.book.title}
                      className="w-full h-48 object-cover rounded-md mb-2"
                    />
                    <p className="text-sm font-semibold text-gray-100 line-clamp-2">
                      {item.book.title}
                    </p>
                    <p className="text-xs text-gray-400 line-clamp-1">
                      {item.book.authors?.join(", ") || "Unknown Author"}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
