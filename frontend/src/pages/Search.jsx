import React, { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { getExploreData } from "../services/bookApi";
import toast from "react-hot-toast";

export default function Search() {
  const location = useLocation();
  const navigate = useNavigate();

  const params = new URLSearchParams(location.search);
  const initialQuery = params.get("q") || "";

  const [query, setQuery] = useState(initialQuery);
  const [results, setResults] = useState([]);
  const [pagination, setPagination] = useState({
    page: 1,
    total_pages: 1,
    total_items: 0,
  });
  const [loading, setLoading] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);

  // ---------------------------------
  // Fetch results when query changes
  // ---------------------------------
  useEffect(() => {
    if (!initialQuery.trim()) return;
    fetchSearchResults(initialQuery, 1, true);
  }, [initialQuery]);

  // ---------------------------------
  // Fetch results (core logic)
  // ---------------------------------
  const fetchSearchResults = async (searchTerm, page = 1, reset = false) => {
    if (reset) setLoading(true);
    else setLoadingMore(true);

    try {
      const { data } = await getExploreData({
        q: searchTerm,
        page,
        page_size: 12, // ⬅️ fetch 12 results per batch
      });

      if (data.mode !== "search") {
        toast.error("Unexpected response mode");
        return;
      }

      setResults((prev) =>
        reset ? data.data.results : [...prev, ...data.data.results]
      );

      setPagination({
        page: data.data.page,
        total_pages: data.data.total_pages,
        total_items: data.data.total_items,
      });
    } catch (error) {
      console.error("Search failed:", error);
      toast.error("Failed to load search results");
    } finally {
      if (reset) setLoading(false);
      else setLoadingMore(false);
    }
  };

  // ---------------------------------
  // Handle search form
  // ---------------------------------
  const handleSearch = (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    navigate(`/search?q=${encodeURIComponent(query.trim())}`);
  };

  // ---------------------------------
  // Load More logic
  // ---------------------------------
  const handleLoadMore = () => {
    if (pagination.page < pagination.total_pages) {
      fetchSearchResults(query, pagination.page + 1, false);
    }
  };

  // ---------------------------------
  // Render
  // ---------------------------------
  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      {/* 🔍 Search Bar */}
      <div className="max-w-4xl mx-auto mt-4 mb-10">
        <form onSubmit={handleSearch} className="relative">
          <input
            type="text"
            placeholder="Search for books, authors, or genres..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
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

      {/* Results Header */}
      {initialQuery && (
        <div className="max-w-6xl mx-auto mb-6 text-center sm:text-left">
          <h2 className="text-2xl font-semibold">
            Results for <span className="text-red-400">“{initialQuery}”</span>
          </h2>
          {pagination.total_items > 0 && (
            <p className="text-sm text-gray-400 mt-1">
              {pagination.total_items} books found
            </p>
          )}
        </div>
      )}

      {/* Results Grid */}
      <div className="max-w-6xl mx-auto">
        {loading ? (
          <div className="flex justify-center py-20">
            <p className="text-gray-400">Loading search results...</p>
          </div>
        ) : results.length > 0 ? (
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

            {/* Load More Button */}
            {pagination.page < pagination.total_pages && (
              <div className="flex justify-center mt-10">
                <button
                  onClick={handleLoadMore}
                  disabled={loadingMore}
                  className="px-6 py-2 bg-red-600 hover:bg-red-700 rounded-lg text-sm font-medium transition disabled:opacity-60"
                >
                  {loadingMore ? "Loading..." : "Load More"}
                </button>
              </div>
            )}
          </>
        ) : (
          <p className="text-gray-500 text-center py-20">
            No books found for this query.
          </p>
        )}
      </div>
    </div>
  );
}
