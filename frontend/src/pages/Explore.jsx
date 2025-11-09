import React, { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import { getExploreData } from "../services/bookApi";
import SectionRow from "../components/SectionRow";

export default function Explore() {
  const navigate = useNavigate();
  const location = useLocation();

  const [mode, setMode] = useState(null);
  const [sections, setSections] = useState({});
  const [results, setResults] = useState([]);
  const [pagination, setPagination] = useState({});
  const [loading, setLoading] = useState(true);
  const [sortOption, setSortOption] = useState("");
  const [searchInput, setSearchInput] = useState("");

  const params = new URLSearchParams(location.search);
  const genre = params.get("genre");
  const sort = params.get("sort");
  const page = parseInt(params.get("page")) || 1;

  useEffect(() => {
    if (sort) setSortOption(sort);
    fetchExploreData();
  }, [genre, sort, page]);

  const fetchExploreData = async () => {
    setLoading(true);
    try {
      const queryParams = {};
      if (genre) queryParams.genre = genre;
      if (sort) queryParams.sort = sort;
      if (page) queryParams.page = page;

      const { data } = await getExploreData(queryParams);
      setMode(data.mode);

      if (data.mode === "default") {
        setSections(data.sections || {});
      } else {
        setResults(data.data.results || []);
        setPagination({
          page: data.data.page,
          total_pages: data.data.total_pages,
          total_items: data.data.total_items,
        });
      }
    } catch {
      toast.error("Failed to fetch explore data");
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    if (!searchInput.trim()) return;
    navigate(`/search?q=${encodeURIComponent(searchInput.trim())}`);
  };

  const handleSortChange = (e) => {
    const newSort = e.target.value;
    setSortOption(newSort);

    const newParams = new URLSearchParams(location.search);
    if (newSort) newParams.set("sort", newSort);
    else newParams.delete("sort");
    newParams.set("page", "1");
    navigate(`/explore?${newParams.toString()}`);
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

      {/* 📚 Explore / Genre / Sorted Views */}
      {loading ? (
        <div className="flex justify-center py-20">
          <p className="text-gray-400">Loading books...</p>
        </div>
      ) : mode === "default" ? (
        <div className="space-y-12">
          {Object.entries(sections).map(([category, books]) => (
            <SectionRow
              key={category}
              category={category}
              books={books}
              onViewAll={() => navigate(`/explore?genre=${category}`)}
            />
          ))}
        </div>
      ) : (
        <div className="max-w-6xl mx-auto">
          {/* Header + Sort */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6">
            <h2 className="text-2xl font-semibold capitalize text-center sm:text-left">
              {mode === "genre" && `${genre} Books`}
              {mode === "sorted" && `Sorted Books (${sort})`}
            </h2>

            <div className="mt-4 sm:mt-0">
              <select
                value={sortOption}
                onChange={handleSortChange}
                className="bg-gray-800 border border-gray-700 text-gray-300 text-sm rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-red-500"
              >
                <option value="">Sort by...</option>
                <option value="newest">Newest</option>
                <option value="popular">Most Popular</option>
                <option value="title">Title (A–Z)</option>
              </select>
            </div>
          </div>

          {/* Results Grid */}
          {results.length > 0 ? (
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
          ) : (
            <p className="text-gray-500 text-center py-20">No books found.</p>
          )}

          {/* Pagination */}
          {pagination.total_pages > 1 && (
            <div className="flex justify-center items-center gap-4 mt-10">
              <button
                disabled={pagination.page <= 1}
                onClick={() => changePage(pagination.page - 1)}
                className="px-4 py-2 bg-gray-800 text-gray-300 rounded-md hover:bg-gray-700 disabled:opacity-50"
              >
                Prev
              </button>
              <span className="text-gray-400">
                Page {pagination.page} of {pagination.total_pages}
              </span>
              <button
                disabled={pagination.page >= pagination.total_pages}
                onClick={() => changePage(pagination.page + 1)}
                className="px-4 py-2 bg-gray-800 text-gray-300 rounded-md hover:bg-gray-700 disabled:opacity-50"
              >
                Next
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
