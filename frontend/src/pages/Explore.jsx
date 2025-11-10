import React, { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import { getExploreData } from "../services/bookApi";

export default function Explore() {
  const navigate = useNavigate();
  const location = useLocation();

  const [mode, setMode] = useState(null);
  const [sections, setSections] = useState({});
  const [results, setResults] = useState([]);
  const [pagination, setPagination] = useState({});
  const [loading, setLoading] = useState(true);
  const [searchInput, setSearchInput] = useState("");

  const params = new URLSearchParams(location.search);
  const genre = params.get("genre");
  const page = parseInt(params.get("page")) || 1;

  useEffect(() => {
    fetchExploreData();
  }, [genre, page]);

  const fetchExploreData = async () => {
    setLoading(true);
    try {
      const queryParams = {};
      if (genre) queryParams.genre = genre;
      if (page) queryParams.page = page;

      const { data } = await getExploreData(queryParams);
      setMode(data.mode || (genre ? "genre" : "default"));

      if (data.mode === "default") {
        // ✅ Move “Science” to the top of sections
        const ordered = Object.entries(data.sections || {}).sort(([keyA], [keyB]) => {
          if (keyA.toLowerCase().includes("science")) return -1;
          if (keyB.toLowerCase().includes("science")) return 1;
          return 0;
        });
        setSections(Object.fromEntries(ordered));
      } else {
        setResults(data.results || []);
        setPagination({
          page: data.page,
          next_page: data.next_page,
          total_items: data.total_items,
        });
      }
    } catch (err) {
      console.error("Explore fetch failed:", err);
      toast.error("Failed to load explore data");
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    if (!searchInput.trim()) return;
    navigate(`/search?q=${encodeURIComponent(searchInput.trim())}`);
  };

  const changePage = (newPage) => {
    const newParams = new URLSearchParams(location.search);
    newParams.set("page", newPage);
    navigate(`/explore?${newParams.toString()}`);
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      {/* 🔍 Search Bar */}
      <div className="max-w-4xl mx-auto mt-4 mb-10">
        <form onSubmit={handleSearch} className="relative">
          <input
            type="text"
            placeholder="Search for books, authors, or genres..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            className="w-full p-4 rounded-2xl bg-gray-800 border border-gray-700 placeholder-gray-400 text-gray-100 focus:outline-none focus:ring-2 focus:ring-red-500"
          />
          <button
            type="submit"
            className="absolute right-3 top-3 px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg text-sm font-medium transition"
          >
            Search
          </button>
        </form>
      </div>

      {/* 📚 Explore / Genre Views */}
      {loading ? (
        <div className="flex justify-center py-20">
          <p className="text-gray-400">Loading books...</p>
        </div>
      ) : mode === "default" ? (
        // 🧱 Horizontal grid per genre section
        <div className="space-y-12 max-w-6xl mx-auto">
          {Object.entries(sections).map(([category, books]) => (
            <div key={category}>
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold capitalize">
                  {category.replace(/_/g, " ")}
                </h2>
                <button
                  onClick={() => navigate(`/explore?genre=${category}`)}
                  className="text-sm text-red-400 hover:text-red-300 transition"
                >
                  View All →
                </button>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-5">
                {books.slice(0, 6).map((book) => (
                  <div
                    key={book.google_id}
                    onClick={() => navigate(`/books/${book.google_id}`)}
                    className="bg-gray-850 border border-gray-700 p-3 rounded-lg hover:border-red-500/60 cursor-pointer transition"
                  >
                    <img
                      src={
                        book.thumbnail ||
                        "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ac/No_image_available.svg/480px-No_image_available.svg.png"
                      }
                      alt={book.title}
                      className="w-full h-48 object-cover rounded-md mb-2"
                      onError={(e) => {
                        e.currentTarget.src =
                          "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ac/No_image_available.svg/480px-No_image_available.svg.png";
                      }}
                    />
                    <h3 className="text-sm font-semibold line-clamp-2">
                      {book.title}
                    </h3>
                    <p className="text-xs text-gray-400 line-clamp-1">
                      {book.authors?.join(", ") || "Unknown Author"}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      ) : (
        // 🎯 Genre-specific paginated view
        <div className="max-w-6xl mx-auto">
          <h2 className="text-2xl font-semibold capitalize mb-6 text-center sm:text-left">
            {genre ? `${genre.replace(/_/g, " ")} Books` : "Explore Books"}
          </h2>

          {results.length > 0 ? (
            <>
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-6">
                {results.map((book) => (
                  <div
                    key={book.google_id}
                    onClick={() => navigate(`/books/${book.google_id}`)}
                    className="bg-gray-850 border border-gray-700 p-3 rounded-lg hover:border-red-500/60 cursor-pointer transition"
                  >
                    <img
                      src={
                        book.thumbnail ||
                        "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ac/No_image_available.svg/480px-No_image_available.svg.png"
                      }
                      alt={book.title}
                      className="w-full h-60 object-cover rounded-md mb-2"
                    />
                    <h3 className="text-sm font-semibold line-clamp-2">
                      {book.title}
                    </h3>
                    <p className="text-xs text-gray-400 line-clamp-1">
                      {book.authors?.join(", ") || "Unknown Author"}
                    </p>
                  </div>
                ))}
              </div>

              {/* Pagination */}
              {pagination.next_page && (
                <div className="flex justify-center mt-10">
                  <button
                    onClick={() => changePage(pagination.next_page)}
                    className="px-6 py-2 bg-red-600 hover:bg-red-700 rounded-lg text-sm font-medium transition"
                  >
                    Load More
                  </button>
                </div>
              )}
            </>
          ) : (
            <p className="text-gray-500 text-center py-20">
              No books found in this category.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
