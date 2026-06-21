import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function RequireAuth({ roles, children }) {
  const { user, loading } = useAuth();

  // ⏳ Wait for auth bootstrap
  if (loading) {
    return (
      <div
        style={{
          height: "100vh",
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          background: "#020617",
          color: "#38bdf8",
          fontWeight: "bold",
        }}
      >
        Loading...
      </div>
    );
  }

  // 🔒 Not logged in
  if (!user) {
    return <Navigate to="/login" replace />;
  }

  // 🔐 Optional role check (ONLY when roles is passed)
  if (roles && Array.isArray(roles)) {
    if (!roles.includes(user.role)) {
      return <Navigate to="/dashboard" replace />;
    }
  }

  // ✅ Authorized
  return children ? children : <Outlet />;
}
