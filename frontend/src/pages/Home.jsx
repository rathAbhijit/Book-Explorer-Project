// src/pages/Home.jsx
import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getHomeData } from "../services/bookApi";
import Carousel from "../components/Carousel";
import SectionBlock from "../components/SectionBlock";

export default function Home() {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [homeData, setHomeData] = useState({
    carousel: [],
    bestsellers: [],
    recent: [],
    cached: false,
  });

  useEffect(() => {
    const fetchData = async () => {
      try {
        const { data } = await getHomeData();
        setHomeData(data);
      } catch (error) {
        console.error("Failed to fetch home data", error);
      }
    };
    fetchData();
  }, []);

  const handleSearch = (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    navigate(`/search?q=${encodeURIComponent(query.trim())}`);
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Search Bar */}
      <div className="w-full max-w-4xl mx-auto mt-8 px-4">
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

      {/* Carousel */}
      <div className="w-full max-w-5xl mx-auto mt-10 px-4">
        <Carousel items={homeData.carousel} />
      </div>

      {/* Cached Indicator */}
      {homeData.cached && (
        <p className="text-xs text-gray-500 text-center mt-2 italic">
          (Loaded from cache)
        </p>
      )}

      {/* Sections */}
      <div className="w-full max-w-6xl mx-auto mt-12 px-6 mb-16 grid grid-cols-1 lg:grid-cols-2 gap-8">
        <SectionBlock
          title="🔥 Popular Now"
          data={homeData.bestsellers}
          isBestseller
          onViewAll={() => navigate("/explore?sort=popular")}
        />
        <SectionBlock
          title="🕓 Recently Added"
          data={homeData.recent}
          onViewAll={() => navigate("/explore?sort=newest")}
        />
      </div>
    </div>
  );
}
