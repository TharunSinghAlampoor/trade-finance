import api from "../api/axios";
import {
  Database,
  FileText,
  ShieldCheck,
  ScrollText,
  FileSpreadsheet,
} from "lucide-react";

export default function Exports() {
  const downloadFile = async (endpoint, filename) => {
    try {
      const res = await api.get(endpoint, {
        responseType: "blob",
      });

      const blob = new Blob([res.data]);
      const url = window.URL.createObjectURL(blob);

      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();

      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Export failed", err);
      alert("Export failed. Backend not reachable.");
    }
  };

  return (
    <div
      className="min-h-screen px-10 py-8"
      style={{
        background:
          "linear-gradient(180deg, #fde5d4 0%, #fbe0cd 50%, #fff1e6 100%)",
        color: "#3f2d20",

        /* 🔥 FONT CHANGE */
        fontFamily:
          "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
      }}
    >
      {/* ===== HEADER ===== */}
      <div className="max-w-6xl mx-auto mb-10">
        <h1
          className="text-2xl font-bold tracking-tight text-[#3f2d20]"
          style={{ fontFamily: "inherit" }}
        >
          Data Exports
        </h1>
        <p className="text-sm text-[#7a5642] mt-1">
          Secure, audited exports generated directly from the ledger
        </p>
      </div>

      {/* ===== EXPORT SECTIONS ===== */}
      <div className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* ================= CSV EXPORTS ================= */}
        <Section title="CSV Exports" subtitle="Structured data for analysis">
          <ExportRow
            icon={Database}
            iconColor="text-blue-700"
            label="Ledger Records"
            desc="Immutable ledger history"
            onClick={() =>
              downloadFile("/exports/csv/ledgers", "ledger.csv")
            }
          />

          <ExportRow
            icon={ScrollText}
            iconColor="text-emerald-700"
            label="Documents"
            desc="All uploaded documents"
            onClick={() =>
              downloadFile("/exports/csv/documents", "documents.csv")
            }
          />

          <ExportRow
            icon={ShieldCheck}
            iconColor="text-amber-700"
            label="Risk Scores"
            desc="Risk analytics and scoring"
            onClick={() =>
              downloadFile("/exports/csv/risk", "risk_scores.csv")
            }
          />

          <ExportRow
            icon={FileSpreadsheet}
            iconColor="text-purple-700"
            label="Trades"
            desc="Trade lifecycle data"
            onClick={() =>
              downloadFile("/exports/csv/trades", "trades.csv")
            }
          />
        </Section>

        {/* ================= PDF EXPORTS ================= */}
        <Section title="PDF Exports" subtitle="Human-readable audit reports">
          <ExportRow
            icon={FileText}
            iconColor="text-rose-700"
            label="Trade Audit Report"
            desc="Complete trade audit trail"
            accent="red"
            onClick={() => {
              const tradeId = prompt("Enter Trade ID");
              if (!tradeId) return;
              downloadFile(
                `/exports/pdf/trade/${tradeId}`,
                `trade_${tradeId}.pdf`
              );
            }}
          />
        </Section>
      </div>

      {/* ===== FOOTNOTE ===== */}
      <div className="max-w-6xl mx-auto mt-14 text-xs text-[#7a5642] border-t border-[#e7c7b2] pt-6">
        All exports are access-controlled, logged, and tamper-evident.
      </div>
    </div>
  );
}

/* ======================================================
   UI COMPONENTS
====================================================== */

function Section({ title, subtitle, children }) {
  return (
    <div
      className="rounded-xl p-6 border shadow-sm"
      style={{
        background: "#fff1e6",
        borderColor: "#f1cbb1",
        fontFamily: "inherit",
      }}
    >
      <h2 className="text-lg font-semibold text-[#3f2d20]">
        {title}
      </h2>
      <p className="text-xs text-[#7a5642] mb-6">
        {subtitle}
      </p>
      <div className="space-y-3">{children}</div>
    </div>
  );
}

function ExportRow({ icon: Icon, iconColor, label, desc, onClick, accent }) {
  const accentStyle =
    accent === "red"
      ? "hover:border-rose-300 hover:bg-rose-50"
      : "hover:border-amber-300 hover:bg-amber-50";

  return (
    <button
      onClick={onClick}
      className={`w-full text-left flex items-center justify-between gap-4 p-4 rounded-lg border transition ${accentStyle}`}
      style={{
        background: "#ffffff",
        borderColor: "#f1cbb1",
        fontFamily: "inherit",
      }}
    >
      <div className="flex items-center gap-4">
        <div
          className="w-10 h-10 rounded-lg flex items-center justify-center"
          style={{ background: "#fde5d4" }}
        >
          <Icon className={`w-5 h-5 ${iconColor}`} />
        </div>

        <div>
          <div className="text-sm font-semibold text-[#3f2d20]">
            {label}
          </div>
          <div className="text-xs text-[#7a5642]">
            {desc}
          </div>
        </div>
      </div>

      <span className="text-[10px] uppercase tracking-widest text-[#7a5642]">
        Download
      </span>
    </button>
  );
}
