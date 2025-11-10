import React, { useState } from "react";
import toast from "react-hot-toast";

export default function Summarizer() {
  const [file, setFile] = useState(null);
  const [maxWords, setMaxWords] = useState(250);
  const [summaryData, setSummaryData] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setSummaryData(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      toast.error("Please upload a file to summarize.");
      return;
    }

    setLoading(true);
    setSummaryData(null);

    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("max_summary_words", maxWords);

      const res = await fetch("http://127.0.0.1:8000/api/v1/summarize/upload/", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) throw new Error("Failed to summarize document.");

      const data = await res.json();
      setSummaryData(data);
      toast.success("Summary generated successfully!");
    } catch (error) {
      console.error("Summarization failed:", error);
      toast.error("Error generating summary. Try again later.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white flex flex-col items-center py-10 px-6">
      <div className="w-full max-w-3xl bg-gray-850 border border-gray-700 rounded-2xl shadow-lg p-8">
        <h1 className="text-2xl font-bold mb-6 text-center text-red-400">
          📄 AI Document Summarizer
        </h1>

        {/* Upload Form */}
        <form onSubmit={handleSubmit} className="flex flex-col gap-6">
          <div>
            <label className="block text-sm text-gray-400 mb-2">
              Upload a file (.pdf / .docx / .txt)
            </label>
            <input
              type="file"
              accept=".pdf,.docx,.txt"
              onChange={handleFileChange}
              className="w-full p-3 rounded-lg bg-gray-800 border border-gray-700 text-gray-300 focus:ring-2 focus:ring-red-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-2">
              Max Summary Words
            </label>
            <input
              type="number"
              min="30"
              max="1200"
              value={maxWords}
              onChange={(e) => setMaxWords(e.target.value)}
              className="w-32 p-2 rounded-lg bg-gray-800 border border-gray-700 text-gray-100 focus:ring-2 focus:ring-red-500 focus:outline-none"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="bg-red-600 hover:bg-red-700 rounded-lg py-3 text-sm font-medium transition disabled:opacity-60"
          >
            {loading ? "Generating Summary..." : "Generate Summary"}
          </button>
        </form>

        {/* Loading Spinner */}
        {loading && (
          <div className="flex justify-center items-center mt-6">
            <div className="w-10 h-10 border-4 border-gray-600 border-t-red-500 rounded-full animate-spin"></div>
          </div>
        )}

        {/* Summary Result */}
        {summaryData && (
          <div className="mt-10 bg-gray-800 border border-gray-700 rounded-xl p-6">
            <h2 className="text-xl font-semibold mb-4 text-red-400">
              🧠 Summary
            </h2>
            <p className="text-gray-200 leading-relaxed whitespace-pre-wrap">
              {summaryData.summary || "No summary available."}
            </p>

            {/* Stats */}
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 text-sm text-gray-400 mt-6">
              <p>
                <span className="font-semibold text-gray-300">Input Words:</span>{" "}
                {summaryData.input_words}
              </p>
              <p>
                <span className="font-semibold text-gray-300">
                  Summary Words:
                </span>{" "}
                {summaryData.summary_words}
              </p>
              <p>
                <span className="font-semibold text-gray-300">
                  Compression Ratio:
                </span>{" "}
                {summaryData.compression_ratio?.toFixed(2)}
              </p>
              <p>
                <span className="font-semibold text-gray-300">Chunks:</span>{" "}
                {summaryData.chunks}
              </p>
              <p>
                <span className="font-semibold text-gray-300">Cached:</span>{" "}
                {summaryData.cached ? "Yes ✅" : "No ❌"}
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
