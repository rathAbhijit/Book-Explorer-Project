import { useState } from "react";
import { useAuth } from "../../context/AuthContext";

export default function RegisterStart() {
  const { registerStart, loading } = useAuth();
  const [form, setForm] = useState({ name: "", email: "", password: "" });

  const handleSubmit = (e) => {
    e.preventDefault();
    registerStart(form);
  };

  return (
    <div className="max-w-md mx-auto bg-gray-800 p-6 rounded-2xl shadow-lg mt-10">
      <h2 className="text-xl font-bold mb-4 text-center text-white">
        Create Account
      </h2>

      <form onSubmit={handleSubmit} className="space-y-4">
        <input
          className="w-full p-2 rounded bg-gray-700 text-white"
          placeholder="Full Name"
          value={form.name}
          onChange={(e) => setForm({ ...form, name: e.target.value })}
          required
        />

        <input
          className="w-full p-2 rounded bg-gray-700 text-white"
          placeholder="Email"
          type="email"
          value={form.email}
          onChange={(e) => setForm({ ...form, email: e.target.value })}
          required
        />

        <input
          className="w-full p-2 rounded bg-gray-700 text-white"
          placeholder="Password"
          type="password"
          value={form.password}
          onChange={(e) => setForm({ ...form, password: e.target.value })}
          required
        />

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-red-500 py-2 rounded hover:bg-red-600 transition text-white"
        >
          {loading ? "Sending OTP..." : "Send OTP"}
        </button>
      </form>
    </div>
  );
}
