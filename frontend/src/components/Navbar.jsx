import React, { useContext } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { ThemeContext } from "../context/ThemeContext";
import { Sun, Moon } from "lucide-react";

export default function Navbar() {
  const { isAuthenticated, logout } = useAuth();
  const { theme, toggleTheme } = useContext(ThemeContext);
  const navigate = useNavigate();

  const navLinkClass = ({ isActive }) =>
    `px-4 py-2 text-sm font-medium rounded-md transition ${
      isActive
        ? "text-red-400 bg-gray-800"
        : "text-gray-300 hover:text-red-400 hover:bg-gray-800"
    }`;

  return (
    <nav className="bg-gray-100 dark:bg-gray-950 border-b border-gray-300 dark:border-gray-800 shadow-md sticky top-0 z-50 transition-colors duration-300">
      <div className="max-w-7xl mx-auto px-6 py-3 flex justify-between items-center">
        {/* 🔸 Logo */}
        <div
          className="flex items-center gap-2 cursor-pointer"
          onClick={() => navigate("/")}
        >
          <img
            src="/logo192.png"
            alt="Book Explorer"
            className="w-8 h-8 rounded-lg"
          />
          <span className="text-xl font-bold text-red-500 tracking-wide">
            Book Explorer
          </span>
        </div>

        {/* 🔹 Nav Links */}
        <div className="hidden md:flex items-center gap-2">
          <NavLink to="/" className={navLinkClass}>
            Home
          </NavLink>

          <NavLink to="/explore" className={navLinkClass}>
            Explore
          </NavLink>

          <NavLink to="/library" className={navLinkClass}>
            Library
          </NavLink>

          <NavLink to="/summarizer" className={navLinkClass}>
            Summarizer
          </NavLink>

          {/* 🌗 Theme Toggle */}
          <button
            onClick={toggleTheme}
            className="p-2 rounded-md border border-gray-400 dark:border-gray-700 bg-gray-200 dark:bg-gray-800 hover:bg-gray-300 dark:hover:bg-gray-700 transition"
            title={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
          >
            {theme === "dark" ? (
              <Sun size={16} className="text-yellow-300" />
            ) : (
              <Moon size={16} className="text-gray-700" />
            )}
          </button>

          {isAuthenticated ? (
            <button
              onClick={logout}
              className="ml-3 px-4 py-2 bg-red-600 hover:bg-red-700 rounded-md text-sm font-medium text-white transition"
            >
              Logout
            </button>
          ) : (
            <button
              onClick={() => navigate("/login")}
              className="ml-3 px-4 py-2 border border-red-600 text-red-400 rounded-md hover:bg-red-600 hover:text-white transition"
            >
              Login
            </button>
          )}
        </div>
      </div>
    </nav>
  );
}
