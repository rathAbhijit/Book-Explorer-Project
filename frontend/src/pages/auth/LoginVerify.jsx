import React, { useState } from "react";
import { useAuth } from "../../context/AuthContext";
import { useNavigate } from "react-router-dom";

export default function LoginVerify() {
  const [otp, setOtp] = useState("");
  const { loginVerify, resend, otpState, loading } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    const result = await loginVerify({ otp });
    if (result !== false) {
      navigate("/explore");
    }
  };

  if (!otpState?.email) {
    return (
      <div className="flex items-center justify-center min-h-screen text-white bg-gray-900">
        <p>No login session found. Please login again.</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-900 text-white px-4">
      <div className="bg-gray-800 w-full max-w-md p-8 rounded-2xl shadow-lg border border-gray-700">
        <h2 className="text-2xl font-bold text-center text-red-400 mb-4">
          Verify Login
        </h2>
        <p className="text-center text-gray-400 mb-6 text-sm">
          Sent to <span className="text-gray-200">{otpState.email}</span>
        </p>

        <form onSubmit={handleSubmit}>
          <input
            type="text"
            placeholder="Enter OTP"
            className="w-full p-3 mb-6 bg-gray-700 rounded focus:outline-none focus:ring-2 focus:ring-red-500"
            value={otp}
            onChange={(e) => setOtp(e.target.value)}
            required
          />

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-red-600 hover:bg-red-700 transition p-3 rounded font-semibold"
          >
            {loading ? "Verifying..." : "Verify & Login"}
          </button>
        </form>

        <div className="text-center mt-6">
          <button
            onClick={resend}
            disabled={loading}
            className="text-sm text-gray-400 hover:text-red-400 transition"
          >
            Resend OTP
          </button>
        </div>
      </div>
    </div>
  );
}
