import React, { useEffect, useState, useMemo } from "react";
import api from "../api/axios";
import { PieChart, Pie, Cell, ResponsiveContainer } from "recharts";
import { RefreshCcw, ShieldAlert, FileText } from "lucide-react";

/* ================= RISK CONFIG ================= */
const RISK_SEGMENTS = [
  { label: "CRITICAL", color: "#ef4444", from: 0, to: 20 }, // red
  { label: "HIGH", color: "#f97316", from: 21, to: 30 },   // orange
  { label: "MEDIUM", color: "#eab308", from: 31, to: 69 }, // yellow
  { label: "LOW", color: "#22c55e", from: 70, to: 100 },   // green
];

const SPEEDOMETER_DATA = Array(4).fill({ value: 25 });

const getRisk = (score = 0) => {
  if (score <= 20) return RISK_SEGMENTS[0];
  if (score <= 30) return RISK_SEGMENTS[1];
  if (score <= 69) return RISK_SEGMENTS[2];
  return RISK_SEGMENTS[3];
};

export default function RiskAnalytics() {
  const [data, setData] = useState([]);
  const [role, setRole] = useState("corp");
  const [loading, setLoading] = useState(true);
  const [selectedUserId, setSelectedUserId] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  /* ================= AUTH ROLE ================= */
  useEffect(() => {
    api
      .get("/auth/me")
      .then((res) => setRole((res.data?.role || "corp").toLowerCase()))
      .catch(() => setRole("corp"));
  }, []);

  const isAdminLike = ["admin", "bank", "auditor"].includes(role);

  /* ================= FETCH RISK ================= */
  const fetchRisk = async () => {
    try {
      setLoading(true);
      setRefreshing(true);

      const endpoint = isAdminLike ? "/risk" : "/risk/me";
      const res = await api.get(endpoint);

      const raw = res.data?.results ?? res.data;
      const list = Array.isArray(raw) ? raw : raw ? [raw] : [];

      setData(list);
      if (list.length) setSelectedUserId((p) => p ?? list[0].user_id);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    if (role) fetchRisk();
  }, [role]);

  const selected = useMemo(
    () => data.find((u) => u.user_id === selectedUserId),
    [data, selectedUserId]
  );

  const risk = selected ? getRisk(selected.score) : RISK_SEGMENTS[3];

  /* ================= LOADING ================= */
  if (loading) {
    return (
      <div
        className="h-screen flex items-center justify-center"
        style={{ background: "#31393C" }}
      >
        <RefreshCcw className="animate-spin text-sky-400" size={32} />
      </div>
    );
  }

  /* ================= UI ================= */
  return (
    <div
      className="h-screen flex flex-col overflow-hidden"
      style={{
        background: "#31393C",
        color: "#E5E7EB",
      }}
    >
      {/* HEADER */}
      <div
        className="flex justify-between items-center px-8 py-6 border-b"
        style={{
          background: "#2A3134",
          borderColor: "#475569",
        }}
      >
        <div className="flex items-center gap-3">
          <ShieldAlert size={24} style={{ color: risk.color }} />
          <h1
            className="text-xl font-black uppercase"
            style={{ color: risk.color }}
          >
            Risk Score – {risk.label}
          </h1>
        </div>

        <button
          onClick={fetchRisk}
          className="flex items-center gap-3 px-6 py-2 text-xs font-bold rounded-full text-white transition"
          style={{
            background: "linear-gradient(135deg, #38bdf8, #6366f1)",
            boxShadow: "0 0 0 1px rgba(255,255,255,0.15)",
          }}
        >
          <RefreshCcw size={16} className={refreshing ? "animate-spin" : ""} />
          RECALCULATE
        </button>
      </div>

      {/* MAIN GRID */}
      <div className="flex-1 grid grid-cols-12 overflow-hidden">
        {/* LEFT — USERS */}
        <div
          className="col-span-3 px-6 py-6 space-y-3 border-r"
          style={{
            background: "#2F3639",
            borderColor: "#475569",
          }}
        >
          <div className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 mb-4">
            {isAdminLike ? "Users" : "Your Account"}
          </div>

          {data.map((u) => {
            const r = getRisk(u.score);
            const active = u.user_id === selectedUserId;

            return (
              <button
                key={u.user_id}
                onClick={() => setSelectedUserId(u.user_id)}
                className="w-full text-left p-4 rounded-xl border transition-all"
                style={{
                  background: active ? "#394246" : "transparent",
                  borderColor: active ? "#64748b" : "transparent",
                }}
              >
                <div className="flex justify-between items-start">
                  <div className="text-sm font-bold text-slate-100">
                    User ID : {u.user_id}
                  </div>
                  <div className="text-xl font-black text-white">
                    {u.score}
                  </div>
                </div>

                <div
                  className="mt-2 text-[10px] font-black uppercase tracking-widest"
                  style={{ color: r.color }}
                >
                  {r.label}
                </div>
              </button>
            );
          })}
        </div>

        {/* CENTER — PIE */}
        <div
          className="col-span-6 flex flex-col items-center justify-center -mt-10"
          style={{ background: "#31393C" }}
        >
          <div className="flex gap-8 mt-6 mb-4">
            {RISK_SEGMENTS.map((r) => (
              <span
                key={r.label}
                className="text-sm font-black tracking-widest"
                style={{ color: r.color }}
              >
                {r.label}
              </span>
            ))}
          </div>

          <div className="relative w-full max-w-[520px] aspect-square">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={SPEEDOMETER_DATA}
                  cx="50%"
                  cy="85%"
                  startAngle={180}
                  endAngle={0}
                  innerRadius="70%"
                  outerRadius="100%"
                  dataKey="value"
                  stroke="none"
                  paddingAngle={4}
                >
                  {RISK_SEGMENTS.map((seg, i) => (
                    <Cell
                      key={i}
                      fill={seg.color}
                      fillOpacity={risk.label === seg.label ? 1 : 0.25}
                    />
                  ))}
                </Pie>
              </PieChart>
            </ResponsiveContainer>

            <div className="absolute inset-0 flex flex-col items-center justify-end pb-14">
              <div className="text-[130px] font-black leading-none text-white">
                {selected?.score || 0}
              </div>
              <div
                className="text-xl font-black tracking-[0.6em] uppercase"
                style={{ color: risk.color }}
              >
                {risk.label}
              </div>
            </div>
          </div>
        </div>

        {/* RIGHT — RATIONALE */}
        <div
          className="col-span-3 p-8 overflow-hidden border-l"
          style={{
            background: "#2F3639",
            borderColor: "#475569",
          }}
        >
          <div className="flex items-center gap-2 text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 mb-6">
            <FileText size={14} /> Full Rationale Report
          </div>

          <div className="space-y-3 overflow-y-auto pr-2">
            {selected?.history && selected.history.length > 0 ? (
              selected.history.map((r, i) => (
                <div
                  key={i}
                  className="p-4 rounded-xl text-xs text-slate-200"
                  style={{
                    background: "#394246",
                    border: "1px solid #475569",
                  }}
                >
                  <span className="text-sky-400 mr-2">/</span>
                  {r}
                </div>
              ))
            ) : (
              <div
                className="p-4 rounded-xl text-xs text-slate-400"
                style={{
                  background: "#394246",
                  border: "1px solid #475569",
                }}
              >
                System baseline processing, no risk events recorded yet.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
