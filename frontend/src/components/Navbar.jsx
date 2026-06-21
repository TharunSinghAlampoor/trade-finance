import React from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import {
  LayoutDashboard,
  FileStack,
  ClipboardList,
  ShieldCheck,
  FileDown,
  Settings,
  LogOut,
  ShieldAlert,
  BarChart3,
  Landmark,
} from "lucide-react";

/**
 * Institutional Seamless Navbar - Deep Obsidian Theme
 * Trade Finance Platform
 * © 2026
 */
export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  // Hide navbar if not authenticated
  if (!user) return null;

  return (
    <nav className="bg-[#0F172A] sticky top-0 z-50 border-b border-emerald-500/10 shadow-xl">
      <div className="max-w-[1600px] mx-auto px-6 lg:px-10">
        <div className="flex justify-between h-20 items-center">

          {/* ================= LEFT: BRAND + NAV ================= */}
          <div className="flex items-center gap-6">

            {/* ===== BRAND / LOGO ===== */}
            <div
              onClick={() => navigate("/dashboard")}
              className="flex items-center gap-3 cursor-pointer group"
            >
              <div className="flex items-center justify-center h-10 w-10 rounded-xl bg-emerald-500/10 border border-emerald-500/30 shadow-lg shadow-emerald-500/10">
                <Landmark size={20} className="text-emerald-400" />
              </div>

              <div className="hidden sm:flex flex-col leading-tight">
                <span className="text-sm font-black tracking-wide text-slate-200 group-hover:text-white">
                  TRADE FINANCE
                </span>
                <span className="text-[10px] uppercase tracking-widest text-emerald-400">
                 BlockChain Technology
                </span>
              </div>
            </div>

            {/* ===== NAV LINKS ===== */}
            <div className="flex items-center space-x-1">
              <NavLink to="/dashboard" icon={<LayoutDashboard size={16} />} label="Dashboard" active={location.pathname === "/dashboard"} />
              <NavLink to="/trades" icon={<FileStack size={16} />} label="Trades" active={location.pathname === "/trades"} />
              <NavLink to="/documents" icon={<ClipboardList size={16} />} label="Documents" active={location.pathname === "/documents"} />
              <NavLink to="/ledger" icon={<ShieldAlert size={16} />} label="Ledger" active={location.pathname === "/ledger"} />
              <NavLink to="/exports" icon={<FileDown size={16} />} label="Reports" active={location.pathname === "/exports"} />
              <NavLink to="/risk" icon={<BarChart3 size={16} />} label="Analytics" active={location.pathname === "/risk"} />

              {/* ===== ADMIN / AUDITOR ===== */}
              {(user.role === "admin" || user.role === "auditor") && (
                <div className="flex items-center ml-4 pl-6 border-l border-slate-700/50 space-x-1">
                  <NavLink to="/integrity" icon={<ShieldCheck size={16} />} label="Integrity" active={location.pathname === "/integrity"} />
                  <NavLink to="/users" icon={<Settings size={16} />} label="Users" active={location.pathname === "/users"} />
                </div>
              )}
            </div>
          </div>

          {/* ================= RIGHT: USER + LOGOUT ================= */}
          <div className="flex items-center gap-8">
            <div className="hidden md:flex flex-col items-end border-r border-slate-700/50 pr-8">
              <span className="text-[10px] font-black text-emerald-400 uppercase tracking-[0.2em] leading-none mb-1.5">
                {user.role?.toUpperCase()}
              </span>
              <span className="text-sm font-bold text-slate-200 leading-none">
                {user.name || "Authorized User"}
              </span>
            </div>

            {/* LOGOUT */}
            <button
              onClick={() => {
                logout();
                navigate("/login");
              }}
              className="flex items-center gap-3 px-5 py-2.5 bg-red-600/10 border border-red-500/20 rounded-xl text-red-500 hover:bg-red-600 hover:text-white transition-all duration-300 group shadow-lg shadow-red-900/10"
            >
              <span className="text-xs font-black uppercase tracking-widest">
                Logout
              </span>
              <LogOut size={18} className="group-hover:translate-x-1 transition-transform" />
            </button>
          </div>

        </div>
      </div>
    </nav>
  );
}

/* ================= NAV LINK ================= */
function NavLink({ to, icon, label, active }) {
  return (
    <Link
      to={to}
      className={`flex items-center gap-2.5 px-4 py-2.5 rounded-xl text-[11px] font-bold uppercase tracking-wider transition-all duration-300 ${
        active
          ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 shadow-lg shadow-emerald-500/10"
          : "text-slate-500 hover:text-slate-100 hover:bg-white/5"
      }`}
    >
      {icon}
      <span>{label}</span>
    </Link>
  );
}
