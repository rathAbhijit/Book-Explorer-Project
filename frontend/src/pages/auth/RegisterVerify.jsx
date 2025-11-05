import { useState } from "react";
import { useAuth } from "../../context/AuthContext";

export default function RegisterVerify() {
  const { registerVerify, resend, otpState, loading } = useAuth();
  const [otp, setOtp] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    registerVerify({ otp });
  };

  return (
    <div className="max-w-md mx-auto bg-gray-800 p-6 rounded-2xl shadow-lg mt-10">
      <h2 className="text-xl font-bold mb-4 text-center text-white">
        Verify Email
      </h2>
      <p className="text-sm text-gray-400 text-center mb-3">
        Sent to {otpState?.email}
      </p>

      <form onSubmit={handleSubmit} className="space-y-4">
        <input
          className="w-full p-2 rounded bg-gray-700 text-white"
          placeholder="6-digit OTP"
          value={otp}
          onChange={(e) => setOtp(e.target.value)}
          required
        />

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-red-500 py-2 rounded hover:bg-red-600 transition text-white"
        >
          {loading ? "Verifying..." : "Verify & Create Account"}
        </button>

        <button
          type="button"
          onClick={resend}
          className="w-full underline text-sm mt-2 text-gray-400 hover:text-red-400"
        >
          Resend OTP
        </button>
      </form>
    </div>
  );
}
