import { Link } from "react-router-dom";

export default function Navbar() {
  return (
    <nav className="bg-gray-800 p-4 shadow-lg">
      <div className="container mx-auto flex justify-between items-center">
        <Link to="/" className="text-xl font-bold text-red-400">Book Explorer</Link>
        <div className="space-x-4">
          <Link to="/explore" className="hover:text-red-400">Explore</Link>
          <Link to="/login" className="hover:text-red-400">Login</Link>
          <Link to="/register" className="hover:text-red-400">Register</Link>
        </div>
      </div>
    </nav>
  );
}
