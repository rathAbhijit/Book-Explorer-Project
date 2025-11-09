import { Routes, Route, Navigate, Link, useLocation } from "react-router-dom";
import { useAuth } from "./context/AuthContext";
import Home from "./pages/Home";
import Explore from "./pages/Explore";
import BookDetails from "./pages/BookDetails";
import LoginStart from "./pages/auth/LoginStart";
import LoginVerify from "./pages/auth/LoginVerify";
import AuthorPage from "./pages/AuthorPage";
import Search from "./pages/Search";
import Summarizer from "./pages/Summarizer";
import RegisterStart from "./pages/auth/RegisterStart";
import RegisterVerify from "./pages/auth/RegisterVerify";

/* --------------------------
   🔹 Updated Navbar Component
--------------------------- */
const Navbar = () => {
  const { user, logout } = useAuth();
  const location = useLocation();

  const isActive = (path) =>
    location.pathname === path
      ? "text-red-400 font-semibold"
      : "text-gray-300 hover:text-red-400";

  return (
    <nav className="bg-gray-950 border-b border-gray-800 shadow sticky top-0 z-50">
      <div className="container mx-auto flex justify-between items-center p-4">
        {/* 🔸 Logo */}
        <Link to="/" className="text-xl font-bold text-red-500 tracking-wide">
          Book Explorer
        </Link>

        {/* 🔹 Links */}
        <div className="flex items-center space-x-5">
          <Link to="/" className={isActive("/")}>
            Home
          </Link>

          <Link to="/explore" className={isActive("/explore")}>
            Explore
          </Link>

          <Link to="/summarizer" className={isActive("/summarizer")}>
            Summarizer
          </Link>

          <Link to="/library" className={isActive("/library")}>
            Library
          </Link>

          {user ? (
            <>
              <span className="text-sm opacity-80">{user?.name || user?.email}</span>
              <button
                onClick={logout}
                className="px-3 py-1 border border-red-600 text-red-400 rounded-md hover:bg-red-600 hover:text-white transition text-sm"
              >
                Logout
              </button>
            </>
          ) : (
            <>
              <Link to="/login" className={isActive("/login")}>
                Login
              </Link>
              <Link to="/register" className={isActive("/register")}>
                Register
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
};

/* --------------------------
   🔒 Private Route Wrapper
--------------------------- */
const PrivateRoute = ({ children }) => {
  const { isAuthenticated } = useAuth();
  return isAuthenticated ? children : <Navigate to="/login" replace />;
};

/* --------------------------
   🚀 Main App Component
--------------------------- */
export default function App() {
  return (
    <div className="bg-gray-900 text-gray-100 min-h-screen">
      <Navbar />
      <div className="container mx-auto px-4 py-6">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/explore" element={<Explore />} />
          <Route path="/books/:google_id" element={<BookDetails />} />
          <Route path="/author/:author_name" element={<AuthorPage />} />
          <Route path="/search" element={<Search />} />

          {/* 🧠 Summarizer Page */}
          <Route path="/summarizer" element={<Summarizer />} />

          {/* Auth */}
          <Route path="/login" element={<LoginStart />} />
          <Route path="/verify-login" element={<LoginVerify />} />
          <Route path="/register" element={<RegisterStart />} />
          <Route path="/verify-register" element={<RegisterVerify />} />

          {/* Protected Example */}
          <Route
            path="/library"
            element={
              <PrivateRoute>
                <div>Library</div>
              </PrivateRoute>
            }
          />

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </div>
    </div>
  );
}
