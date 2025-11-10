import React, { useState } from "react";

export default function ReviewSection({ reviews, user, onReviewAction }) {
  const [rating, setRating] = useState(0);
  const [comment, setComment] = useState("");

  return (
    <div className="bg-gray-850 border border-gray-700 rounded-2xl p-6 shadow-md">
      <h3 className="text-lg font-semibold mb-4">User Reviews</h3>

      {user ? (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            onReviewAction({ rating, comment }, "create");
            setRating(0);
            setComment("");
          }}
          className="mb-6"
        >
          <div className="flex items-center gap-3 mb-2">
            {[1, 2, 3, 4, 5].map((n) => (
              <span
                key={n}
                onClick={() => setRating(n)}
                className={`cursor-pointer text-2xl ${
                  n <= rating ? "text-yellow-400" : "text-gray-600"
                }`}
              >
                ★
              </span>
            ))}
          </div>
          <textarea
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder="Write your review..."
            className="w-full p-3 bg-gray-800 rounded-lg text-gray-200 border border-gray-700 mb-3"
          />
          <button
            type="submit"
            className="px-4 py-2 bg-red-600 hover:bg-red-700 rounded-md text-sm"
          >
            Submit Review
          </button>
        </form>
      ) : (
        <p className="text-gray-400 mb-4">Login to write a review.</p>
      )}

      {reviews?.length ? (
        reviews.map((r) => (
          <div
            key={r.id}
            className="border-t border-gray-700 pt-3 mt-3 text-gray-300"
          >
            <p className="font-semibold">
              {r.username}{" "}
              <span className="text-yellow-400 ml-1">{"★".repeat(r.rating)}</span>
            </p>
            <p className="text-sm text-gray-400">{r.comment}</p>
          </div>
        ))
      ) : (
        <p className="text-gray-500 text-sm">No reviews yet.</p>
      )}
    </div>
  );
}
