import { Routes, Route, Navigate } from "react-router-dom";
import RequireAuth from "./auth/RequireAuth";
import Navbar from "./components/Navbar";

// Auth and General Pages
import Login from "./auth/Login";
import Register from "./auth/Register";
import Dashboard from "./pages/Dashboard";
import Profile from "./pages/Profile";

// Feature Pages
import Documents from "./pages/Documents";
import Ledger from "./pages/Ledger";
import Risk from "./pages/Risk";
import Trades from "./pages/Trades";
import TradeDetails from "./pages/TradeDetails";
import Users from "./pages/Users";
import IntegrityDashboard from "./pages/IntegrityDashboard";
import Exports from "./pages/Exports"; // ✅ ADD THIS

export default function App() {
  return (
    <>
      <Navbar />
      <Routes>
        {/* ================= PUBLIC ROUTES ================= */}
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        {/* ================= PROTECTED ROUTES ================= */}
        <Route
          path="/dashboard"
          element={
            <RequireAuth>
              <Dashboard />
            </RequireAuth>
          }
        />

        <Route
          path="/profile"
          element={
            <RequireAuth>
              <Profile />
            </RequireAuth>
          }
        />

        <Route
          path="/documents"
          element={
            <RequireAuth>
              <Documents />
            </RequireAuth>
          }
        />

        <Route
          path="/ledger"
          element={
            <RequireAuth>
              <Ledger />
            </RequireAuth>
          }
        />

        <Route
          path="/risk"
          element={
            <RequireAuth>
              <Risk />
            </RequireAuth>
          }
        />

        {/* ================= TRADE ROUTES ================= */}
        <Route
          path="/trades"
          element={
            <RequireAuth>
              <Trades />
            </RequireAuth>
          }
        />

        <Route
          path="/trades/:tradeId"
          element={
            <RequireAuth>
              <TradeDetails />
            </RequireAuth>
          }
        />

        {/* ================= EXPORTS ================= */}
        <Route
          path="/exports"
          element={
            <RequireAuth>
              <Exports />
            </RequireAuth>
          }
        />

        {/* ================= ADMIN / AUDITOR ROUTES ================= */}
        <Route
          path="/users"
          element={
            <RequireAuth roles={["admin", "auditor"]}>
              <Users />
            </RequireAuth>
          }
        />

        <Route
          path="/integrity"
          element={
            <RequireAuth roles={["admin", "auditor"]}>
              <IntegrityDashboard />
            </RequireAuth>
          }
        />

        {/* ================= DEFAULT ================= */}
        <Route path="*" element={<Navigate to="/dashboard" />} />
      </Routes>
    </>
  );
}
