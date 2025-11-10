import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { getAuthorDetails, getMoreFromAuthor } from "../services/bookApi";
import toast from "react-hot-toast";
import AuthorBooks from "../components/AuthorBooks";
import Skeleton from "../components/Skeleton";
import { ArrowLeft } from "lucide-react";

export default function AuthorPage() {
  const { author_name } = useParams();
  const navigate = useNavigate();

  const [authorInfo, setAuthorInfo] = useState(null);
  const [authorBooks, setAuthorBooks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadingBooks, setLoadingBooks] = useState(true);

  useEffect(() => {
    fetchAuthorDetails();
  }, [author_name]);

  // ------------------------------------------------------
  // Fetch Author Info
  // ------------------------------------------------------
  const fetchAuthorDetails = async () => {
    setLoading(true);
    try {
      const { data } = await getAuthorDetails(author_name);
      setAuthorInfo(data);
      fetchAuthorBooks(author_name);
    } catch (error) {
      console.error("Failed to load author info:", error);
      toast.error("Failed to load author details");
    } finally {
      setLoading(false);
    }
  };

  // ------------------------------------------------------
  // Fetch Books From Author
  // ------------------------------------------------------
  const fetchAuthorBooks = async (name) => {
    setLoadingBooks(true);
    try {
      const { data } = await getMoreFromAuthor(name);
      setAuthorBooks(data.books || []);
    } catch (error) {
      console.error("Failed to load books:", error);
      setAuthorBooks([]);
    } finally {
      setLoadingBooks(false);
    }
  };

  // ------------------------------------------------------
  // Render
  // ------------------------------------------------------
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">
        <p className="text-gray-400">Loading author details...</p>
      </div>
    );
  }

  if (!authorInfo) {
    return (
      <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">
        <p className="text-gray-400">Author not found.</p>
      </div>
    );
  }

  const {
    name,
    bio,
    top_subjects,
    active_years,
    birth_date,
    death_date,
    top_work,
    work_count,
  } = authorInfo;

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6 flex flex-col items-center">
      <div className="w-full max-w-5xl flex flex-col gap-8">
        {/* ======================= BACK BUTTON ======================= */}
        <div className="flex items-center mb-2">
          <button
            onClick={() => navigate(-1)}
            className="flex items-center gap-2 text-sm text-gray-400 hover:text-red-400 transition"
          >
            <ArrowLeft size={18} />
            Back to previous
          </button>
        </div>

        {/* ======================= AUTHOR INFO CARD ======================= */}
        <div className="bg-gray-850 border border-gray-700 rounded-2xl p-6 shadow-lg">
          <h1 className="text-3xl font-bold text-red-400 mb-2">{name}</h1>

          {bio ? (
            <p className="text-gray-300 text-sm mb-3 leading-relaxed">{bio}</p>
          ) : (
            <p className="text-gray-500 italic mb-3">
              No biography available for this author.
            </p>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-gray-300 text-sm mt-3">
            <p>
              <span className="text-gray-400">Active Years:</span>{" "}
              {active_years || "Unknown"}
            </p>
            <p>
              <span className="text-gray-400">Top Work:</span>{" "}
              {top_work || "Not listed"}
            </p>
            <p>
              <span className="text-gray-400">Work Count:</span>{" "}
              {work_count || "N/A"}
            </p>
            <p>
              <span className="text-gray-400">Born:</span>{" "}
              {birth_date || "Unknown"}
            </p>
            <p>
              <span className="text-gray-400">Died:</span>{" "}
              {death_date || "Unknown"}
            </p>
          </div>

          {/* Top Subjects */}
          {top_subjects && top_subjects.length > 0 && (
            <div className="mt-5">
              <h3 className="text-lg font-semibold text-gray-200 mb-2">
                Top Subjects
              </h3>
              <div className="flex flex-wrap gap-2">
                {top_subjects.map((subject, i) => (
                  <span
                    key={i}
                    className="bg-gray-800 border border-gray-700 text-gray-300 text-xs px-3 py-1 rounded-full"
                  >
                    {subject}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* ======================= AUTHOR BOOKS SECTION ======================= */}
        {loadingBooks ? (
          <div className="bg-gray-850 border border-gray-700 rounded-2xl p-6 animate-pulse">
            <Skeleton className="h-5 w-1/3 mb-4" />
            <div className="flex gap-3">
              {[1, 2, 3, 4].map((i) => (
                <Skeleton key={i} className="h-56 w-40 rounded-md" />
              ))}
            </div>
          </div>
        ) : (
          <AuthorBooks books={authorBooks} author={name} />
        )}
      </div>
    </div>
  );
}
