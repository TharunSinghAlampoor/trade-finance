import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Sidebar() {
  const { user } = useAuth(); // Access user role from auth_routes.py

  return (
    <div className="w-64 bg-gray-800 min-h-screen p-6 border-r border-gray-700">
      <nav className="space-y-4">
        <Link to="/dashboard" className="block text-gray-300 hover:text-white">Dashboard</Link>
        <Link to="/documents" className="block text-gray-300 hover:text-white">Documents</Link>
        <Link to="/ledger" className="block text-gray-300 hover:text-white">Audit Ledger</Link>
        
        {/* Strictly map this to /users, NOT /trades */}
        {(user?.role === "admin" || user?.role === "auditor") && (
          <Link to="/users" className="block text-blue-400 font-bold border-t border-gray-700 pt-4">
            User Management
          </Link>
        )}
      </nav>
    </div>
  );
}