import { Routes, Route, Navigate, Link } from "react-router-dom";
import { useAuth } from "./context/AuthContext";
import Home from "./pages/Home";
import Explore from "./pages/Explore";
import LoginStart from "./pages/auth/LoginStart";
import LoginVerify from "./pages/auth/LoginVerify";
import RegisterStart from "./pages/auth/RegisterStart";
import RegisterVerify from "./pages/auth/RegisterVerify";

const Navbar = () => {
  const { user, logout } = useAuth();
  return (
    <nav className="bg-gray-800 p-4 shadow">
      <div className="container mx-auto flex justify-between">
        <Link to="/" className="text-red-400 font-bold">Book Explorer</Link>
        <div className="space-x-4">
          <Link to="/explore" className="hover:text-red-400">Explore</Link>
          {user ? (
            <>
              <span className="text-sm opacity-80">{user?.name || user?.email}</span>
              <button onClick={logout} className="hover:text-red-400">Logout</button>
            </>
          ) : (
            <>
              <Link to="/login" className="hover:text-red-400">Login</Link>
              <Link to="/register" className="hover:text-red-400">Register</Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
};

const PrivateRoute = ({ children }) => {
  const { isAuthenticated } = useAuth();
  return isAuthenticated ? children : <Navigate to="/login" replace />;
};

export default function App() {
  return (
    <div className="bg-gray-900 text-gray-100 min-h-screen">
      <Navbar />
      <div className="container mx-auto px-4 py-6">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/explore" element={<Explore />} />

          {/* Auth */}
          <Route path="/login" element={<LoginStart />} />
          <Route path="/verify-login" element={<LoginVerify />} />
          <Route path="/register" element={<RegisterStart />} />
          <Route path="/verify-register" element={<RegisterVerify />} />

          {/* Example protected route: Library (add page later) */}
          <Route path="/library" element={<PrivateRoute><div>Library</div></PrivateRoute>} />

          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </div>
    </div>
  );
}
