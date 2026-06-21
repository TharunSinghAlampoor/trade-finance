import { useEffect, useState } from "react";
import api from "../api/axios";
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

/* ================= CONSTANTS ================= */
const STATUS_COLORS = {
  PASS: "#22c55e",
  FAIL: "#ef4444",
  PENDING: "#f59e0b",
};

/* ================= COMPONENT ================= */
export default function IntegrityDashboard() {
  const [summary, setSummary] = useState({
    PASS: 0,
    FAIL: 0,
    PENDING: 0,
  });
  const [records, setRecords] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [statusFilter, setStatusFilter] = useState("");
  const [loading, setLoading] = useState(false);

  /* ================= API CALLS ================= */
  const loadSummary = async () => {
    const res = await api.get("/integrity/summary");
    setSummary(res.data);
  };

  const loadRecords = async () => {
    const res = await api.get("/integrity/records", {
      params: statusFilter ? { status: statusFilter } : {},
    });
    setRecords(res.data);
  };

  const loadAlerts = async () => {
    const res = await api.get("/integrity/alerts", {
      params: { acknowledged: false },
    });
    setAlerts(res.data);
  };

  const runIntegrityCheck = async () => {
    setLoading(true);
    try {
      await api.post("/integrity/run");
      await Promise.all([loadSummary(), loadRecords(), loadAlerts()]);
    } finally {
      setLoading(false);
    }
  };

  const acknowledgeAlert = async (alertId) => {
    await api.post(`/integrity/alerts/${alertId}/ack`);
    loadAlerts();
  };

  /* ================= EFFECTS ================= */
  useEffect(() => {
    loadSummary();
    loadRecords();
    loadAlerts();
  }, []);

  useEffect(() => {
    loadRecords();
  }, [statusFilter]);

  /* ================= CHART DATA ================= */
  const pieData = Object.keys(summary).map((k) => ({
    name: k,
    value: summary[k],
  }));

  const barData = [
    { name: "PASS", count: records.filter(r => r.status === "PASS").length },
    { name: "FAIL", count: records.filter(r => r.status === "FAIL").length },
    { name: "PENDING", count: records.filter(r => r.status === "PENDING").length },
  ];

  /* ================= UI ================= */
  return (
    <div
      className="p-6 space-y-8 min-h-screen"
      style={{
        fontFamily:
          "'Inter', system-ui, -apple-system, BlinkMacSystemFont, sans-serif",
        background:
          "linear-gradient(180deg, #BADDFF 0%, #d6efff 50%, #eef8ff 100%)",
        color: "#0f172a",
      }}
    >
      <style>{`
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');
      `}</style>

      <h1 className="text-2xl font-bold text-slate-900">
        Integrity Dashboard
      </h1>

      {/* ===== SUMMARY CARDS ===== */}
      <div className="grid grid-cols-3 gap-4">
        {Object.keys(summary).map((key) => (
          <div
            key={key}
            className="rounded-xl p-4 font-semibold border"
            style={{
              background: "#f5fbff",
              borderColor: "#9accef",
            }}
          >
            <div className="text-sm text-sky-800">{key}</div>
            <div className="text-2xl" style={{ color: STATUS_COLORS[key] }}>
              {summary[key]}
            </div>
          </div>
        ))}
      </div>

      {/* ===== CHARTS ===== */}
      <div className="grid grid-cols-2 gap-6">
        <div
          className="p-4 rounded-xl shadow border h-80"
          style={{
            background: "#f0f9ff",
            borderColor: "#9accef",
          }}
        >
          <h2 className="font-semibold mb-2 text-sky-900">
            Integrity Status Distribution
          </h2>
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie data={pieData} dataKey="value" label>
                {pieData.map((d) => (
                  <Cell key={d.name} fill={STATUS_COLORS[d.name]} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  backgroundColor: "#ffffff",
                  border: "1px solid #9accef",
                  color: "#0f172a",
                }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div
          className="p-4 rounded-xl shadow border h-80"
          style={{
            background: "#f0f9ff",
            borderColor: "#9accef",
          }}
        >
          <h2 className="font-semibold mb-2 text-sky-900">
            Integrity Check Counts
          </h2>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={barData}>
              <XAxis dataKey="name" stroke="#075985" />
              <YAxis stroke="#075985" />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#ffffff",
                  border: "1px solid #9accef",
                  color: "#0f172a",
                }}
              />
              <Bar dataKey="count">
                {barData.map((d) => (
                  <Cell key={d.name} fill={STATUS_COLORS[d.name]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* ===== RUN CHECK ===== */}
      <button
        onClick={runIntegrityCheck}
        disabled={loading}
        className="px-4 py-2 rounded font-semibold text-white"
        style={{
          background: "linear-gradient(135deg, #38bdf8, #0ea5e9)",
          opacity: loading ? 0.6 : 1,
        }}
      >
        {loading ? "Running..." : "Run Integrity Check"}
      </button>

      {/* ===== FILTER ===== */}
      <select
        value={statusFilter}
        onChange={(e) => setStatusFilter(e.target.value)}
        className="px-3 py-2 rounded border"
        style={{
          background: "#ffffff",
          borderColor: "#9accef",
          color: "#0f172a",
        }}
      >
        <option value="">All</option>
        <option value="PASS">PASS</option>
        <option value="FAIL">FAIL</option>
        <option value="PENDING">PENDING</option>
      </select>

      {/* ===== RECORDS TABLE ===== */}
      <div
        className="overflow-x-auto rounded-xl shadow border"
        style={{
          background: "#f5fbff",
          borderColor: "#9accef",
        }}
      >
        <table className="min-w-full text-sm">
          <thead style={{ background: "#e6f4ff" }}>
            <tr>
              {["ID", "Doc ID", "Status", "Stored Hash", "Computed Hash", "Checked At"].map(h => (
                <th
                  key={h}
                  className="p-2 border"
                  style={{
                    borderColor: "#c7e3f7",
                    color: "#075985",
                  }}
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {records.map((r) => (
              <tr key={r.id} className="hover:bg-sky-100">
                <td className="p-2 border border-sky-200 font-mono">{r.id}</td>
                <td className="p-2 border border-sky-200 font-mono">{r.doc_id}</td>
                <td
                  className="p-2 border border-sky-200 font-semibold"
                  style={{ color: STATUS_COLORS[r.status] }}
                >
                  {r.status}
                </td>
                <td className="p-2 border border-sky-200 break-all max-w-xs font-mono">
                  {r.stored_hash}
                </td>
                <td className="p-2 border border-sky-200 break-all max-w-xs font-mono">
                  {r.computed_hash || "-"}
                </td>
                <td className="p-2 border border-sky-200">
                  {new Date(r.created_at).toLocaleString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* ===== ALERTS ===== */}
      <div>
        <h2 className="text-xl font-semibold text-slate-900">
          Active Integrity Alerts
        </h2>

        {alerts.length === 0 && (
          <p className="text-sky-700">No active alerts</p>
        )}

        <div className="space-y-3">
          {alerts.map((a) => (
            <div
              key={a.id}
              className="p-4 rounded-xl border-l-4"
              style={{
                background: "#fff1f2",
                borderLeftColor: "#ef4444",
              }}
            >
              <div className="font-semibold text-red-600">
                {a.alert_type}
              </div>
              <div className="text-sm text-slate-700">
                {a.message}
              </div>
              <button
                onClick={() => acknowledgeAlert(a.id)}
                className="mt-2 px-3 py-1 rounded font-semibold text-white"
                style={{ background: "#16a34a" }}
              >
                Acknowledge
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
