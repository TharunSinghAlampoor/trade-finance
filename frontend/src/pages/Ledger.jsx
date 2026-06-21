import { useEffect, useState } from "react";
import axios from "../api/axios";
import { useAuth } from "../context/AuthContext";
import { FiActivity, FiPlusCircle, FiHash, FiFileText } from "react-icons/fi";

export default function Ledger() {
  const { user } = useAuth();

  const [entries, setEntries] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [eventType, setEventType] = useState("");
  const [description, setDescription] = useState("");
  const [docId, setDocId] = useState("");
  const [tradeId, setTradeId] = useState("");
  const [hashBefore, setHashBefore] = useState("");
  const [hashAfter, setHashAfter] = useState("");
  const [creating, setCreating] = useState(false);
  const [createMsg, setCreateMsg] = useState("");

  useEffect(() => {
    let mounted = true;

    async function loadLedger() {
      try {
        const [entriesRes, statsRes] = await Promise.all([
          axios.get("/ledger/entries"),
          axios.get("/ledger/status"),
        ]);

        if (mounted) {
          setEntries(entriesRes.data);
          setStats(statsRes.data);
        }
      } catch {
        setError("Failed to load ledger data");
      } finally {
        if (mounted) setLoading(false);
      }
    }

    loadLedger();
    return () => (mounted = false);
  }, []);

  function isDuplicate(payload) {
    return entries.some(
      (e) =>
        e.event_type === payload.event_type &&
        e.doc_id === payload.doc_id &&
        e.trade_id === payload.trade_id &&
        e.hash_before === payload.hash_before &&
        e.hash_after === payload.hash_after
    );
  }

  async function createLedgerEntry(e) {
    e.preventDefault();
    setCreateMsg("");

    if (!eventType || !description || !hashAfter) {
      setCreateMsg("Event Type, Description, and Hash After are required.");
      return;
    }

    if (!docId && !tradeId) {
      setCreateMsg("Either Document ID or Trade ID is required.");
      return;
    }

    const payload = {
      event_type: eventType.trim(),
      description: description.trim(),
      doc_id: docId ? Number(docId) : null,
      trade_id: tradeId ? Number(tradeId) : null,
      hash_before: hashBefore || null,
      hash_after: hashAfter.trim(),
    };

    if (isDuplicate(payload)) {
      setCreateMsg("Duplicate ledger entry detected.");
      return;
    }

    try {
      setCreating(true);
      await axios.post("/ledger/entries", payload);
      setCreateMsg("Ledger entry created successfully");

      setEventType("");
      setDescription("");
      setDocId("");
      setTradeId("");
      setHashBefore("");
      setHashAfter("");

      const res = await axios.get("/ledger/entries");
      setEntries(res.data);
    } catch {
      setCreateMsg("Failed to create ledger entry");
    } finally {
      setCreating(false);
    }
  }

  if (!user) return null;
  if (loading) return <p style={{ padding: 24, color: "#334155" }}>Loading ledger…</p>;
  if (error) return <p style={{ padding: 24, color: "#b91c1c" }}>{error}</p>;

  return (
    <div className="ledger-root">
      <style>{`
        .ledger-root {
          min-height: 100vh;
          padding: 24px;
          background: #90D5FF;
          color: #0B1F33;
          font-family: system-ui, -apple-system, BlinkMacSystemFont;
        }

        /* ===== CARD BASE ===== */
        .card {
          border-radius: 16px;
          padding: 24px;
          border: 1px solid transparent;
        }

        /* ===== CARD VARIANTS ===== */
        .card-form {
          background: #EAF7FF;
          border-color: #38BDF8;
          box-shadow: 0 12px 28px rgba(2,132,199,0.25);
        }

        .card-stat {
          background: #ECFEFF;
          border-color: #67E8F9;
          box-shadow: 0 8px 20px rgba(14,165,233,0.25);
        }

        .card-table {
          background: #F0F9FF;
          border: 1px solid #7DD3FC;
          border-radius: 14px;
          overflow: hidden;
        }

        .input-upload {
          width: 100%;
          background: #FFFFFF;
          border: 1px solid #38BDF8;
          border-radius: 10px;
          padding: 12px 16px;
          color: #0B1F33;
          font-size: 14px;
          font-weight: 500;
        }

        .input-upload::placeholder {
          color: #475569;
        }

        .input-upload:focus {
          outline: none;
          border-color: #0284c7;
          box-shadow: 0 0 0 2px rgba(2,132,199,0.35);
        }

        .btn-primary {
          background: linear-gradient(135deg, #0284c7, #2563eb);
          color: #ffffff;
          font-weight: 700;
          padding: 10px 28px;
          border-radius: 10px;
          border: none;
          cursor: pointer;
          box-shadow: 0 6px 18px rgba(2,132,199,0.45);
        }

        table {
          width: 100%;
          border-collapse: collapse;
        }

        th {
          background: #D6F0FF;
          color: #0B1F33;
          font-size: 13px;
          font-weight: 700;
          padding: 12px;
          border-bottom: 1px solid #93C5FD;
        }

        td {
          padding: 10px 12px;
          border-bottom: 1px solid #BAE6FD;
          color: #1E293B;
          font-size: 13px;
          font-weight: 500;
        }

        tr:hover {
          background: #E0F2FE;
        }
      `}</style>

      {/* HEADER */}
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 24 }}>
        <FiActivity size={22} color="#0284c7" />
        <h1 style={{ fontSize: 22, fontWeight: 800 }}>Ledger</h1>
      </div>

      {/* CREATE LEDGER */}
      <form onSubmit={createLedgerEntry} className="card card-form">
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 20, color: "#0284c7", fontWeight: 700 }}>
          <FiPlusCircle /> Create Ledger Entry
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 16, marginBottom: 16 }}>
          <input className="input-upload" placeholder="Event Type" value={eventType} onChange={e => setEventType(e.target.value)} />
          <input className="input-upload" placeholder="Description" value={description} onChange={e => setDescription(e.target.value)} />
          <input className="input-upload" placeholder="Document ID" value={docId} onChange={e => setDocId(e.target.value)} />
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 16, marginBottom: 20 }}>
          <input className="input-upload" placeholder="Trade ID" value={tradeId} onChange={e => setTradeId(e.target.value)} />
          <input className="input-upload" placeholder="Hash Before" value={hashBefore} onChange={e => setHashBefore(e.target.value)} />
          <input className="input-upload" placeholder="Hash After" value={hashAfter} onChange={e => setHashAfter(e.target.value)} />
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <button className="btn-primary" disabled={creating}>
            {creating ? "Creating…" : "Create Ledger"}
          </button>
          {createMsg && <span style={{ color: "#166534", fontWeight: 700 }}>{createMsg}</span>}
        </div>
      </form>

      {/* STATS */}
      {stats && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 16, marginTop: 24 }}>
          <Stat title="Total Entries" value={stats.total_entries} icon={<FiFileText />} />
          {Object.entries(stats.by_event_type || {}).map(([k, v]) => (
            <Stat key={k} title={k} value={v} icon={<FiHash />} />
          ))}
        </div>
      )}

      {/* TABLE */}
      <div className="card card-table" style={{ marginTop: 24 }}>
        <table>
          <thead>
            <tr>
              <th>ID</th><th>Event</th><th>Description</th><th>Trade</th>
              <th>Document</th><th>User</th><th>Org</th><th>Time</th>
            </tr>
          </thead>
          <tbody>
            {entries.map(e => (
              <tr key={e.id}>
                <td>{e.id}</td>
                <td style={{ color: "#0284c7", fontWeight: 800 }}>{e.event_type}</td>
                <td>{e.description}</td>
                <td>{e.trade_id ?? "—"}</td>
                <td>{e.doc_id ?? "—"}</td>
                <td>{e.user_id}</td>
                <td>{e.org_id}</td>
                <td>{new Date(e.created_at).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function Stat({ title, value, icon }) {
  return (
    <div className="card card-stat">
      <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13, fontWeight: 700, color: "#0369A1" }}>
        {icon} {title}
      </div>
      <div style={{ fontSize: 22, fontWeight: 800 }}>{value}</div>
    </div>
  );
}
