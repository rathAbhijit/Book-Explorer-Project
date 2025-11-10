import React from "react";

export default function SummaryCard({ summary, onGenerate }) {
  return (
    <div className="bg-gray-850 border border-gray-700 rounded-2xl p-6 shadow-md">
      <h3 className="text-lg font-semibold mb-3 text-red-400">AI Summary</h3>
      {summary ? (
        <p className="text-gray-300 leading-relaxed">{summary}</p>
      ) : (
        <button
          onClick={onGenerate}
          className="px-4 py-2 bg-red-600 hover:bg-red-700 rounded-md text-sm font-medium"
        >
          Generate Summary
        </button>
      )}
    </div>
  );
}
