import { useEffect, useState } from "react";
import api from "../api/axios";

export default function Trades() {
  const [me, setMe] = useState(null);
  const [trades, setTrades] = useState([]);
  const [selectedTrade, setSelectedTrade] = useState(null); // Amazon-style tracker state
  const [search, setSearch] = useState("");

  const [createForm, setCreateForm] = useState({
    buyer_email: "",
    seller_email: "",
    description: "",
    amount: "",
    currency: "INR",
    remarks: "",
    expected_completion_date: "",
  });

  const [assign, setAssign] = useState({ tradeId: null, bankEmail: "" });
  const [docUpload, setDocUpload] = useState({ tradeId: null, docType: "Commercial Invoice", file: null });

  const [remarkModal, setRemarkModal] = useState({
    tradeId: null,
    action: "",
    remarks: "",
  });

  // workflow sequence for the Amazon-style tracker
  const workflowStages = [
  { key: "initiated", label: "Trade Initiated" },
  { key: "seller_confirmed", label: "Seller Accepted" },
  { key: "documents_uploaded", label: "Seller Documents Uploaded" },
  { key: "bank_assigned", label: "Bank Assigned" },
  { key: "bank_reviewing", label: "Bank Reviewing" },
  { key: "bank_approved", label: "Bank Approved" },
  { key: "bank_documents_uploaded", label: "Bank Documents Uploaded" },
  { key: "payment_released", label: "Funds Released" },
  { key: "completed", label: "Completed" },
];

  useEffect(() => {
    load();
  }, []);

  async function load() {
    try {
      const meRes = await api.get("/auth/me");
      const tradesRes = await api.get("/trades");

      setMe(meRes.data);
      setTrades(tradesRes.data || []);

      setCreateForm((p) => ({
        ...p,
        buyer_email: meRes.data?.email || "",
      }));
    } catch (err) {
      console.error("Initialization error:", err);
    }
  }

  /* ================= ROLES & FILTERS ================= */
  const isCorp = () => me?.role === "corp";
  const isBank = () => me?.role === "bank";
  const isAdmin = () => me?.role === "admin";

  const isBuyer = (t) => isCorp() && t.buyer_id === me?.id;
  const isSeller = (t) => isCorp() && t.seller_id === me?.id;
  const isAssignedBank = (t) => isBank() && t.bank_id === me?.id;

  const isAuditor = () => me?.role === "auditor";

const filteredTrades = (trades || [])
  .filter(t => {
    if (isAdmin() || isAuditor()) return true;
    if (isBank()) return t.bank_id === me?.id;
    return t.buyer_id === me?.id || t.seller_id === me?.id;
  })
 .filter(t => {
  if (!search.trim()) return true;

  const q = search.toLowerCase();

  return (
    String(t?.id || "").includes(q) ||
    String(formatTradeNo(t) || "").toLowerCase().includes(q) ||
    String(t?.description || "").toLowerCase().includes(q) ||
    String(t?.status || "").toLowerCase().includes(q) ||
    String(`${t?.currency || ""} ${t?.amount || ""}`)
      .toLowerCase()
      .includes(q)
  );
});

  /* ================= DASHBOARD COUNTS ================= */
 const statusCounts = (trades || []).reduce(
  (acc, t) => {
    acc.total += 1;
    acc[t.status] = (acc[t.status] || 0) + 1;
    return acc;
  },
  { total: 0 }
);

  /* ================= HELPERS ================= */
  const formatTradeNo = (trade) => {
  if (!trade) return "";
  if (trade.trade_num) return String(trade.trade_num);

  const id = trade?.id;
  if (typeof id !== "number") return "";

  return `TRX-${String(id).padStart(6, "0")}`;
};
    
    
  const formatTime = (iso) => {
    if (!iso) return null;
    return new Date(iso).toLocaleString([], { 
        month: 'short', 
        day: 'numeric', 
        hour: '2-digit', 
        minute: '2-digit' 
    });
  };

  /* ================= API ACTIONS ================= */
  async function createTrade(e) {
    e.preventDefault();
    if (!createForm.expected_completion_date) {
      alert("Expected completion date is required");
      return;
    }

    try {
      const res = await api.post("/trades", null, {
        params: {
          ...createForm,
          amount: Number(createForm.amount),
          currency: createForm.currency,
        },
      });

      const tradeId = res.data.id;
      await api.patch(`/trades/${tradeId}/expected-date`, {
        expected_completion_date: createForm.expected_completion_date,
      });

      setCreateForm({
        buyer_email: me?.email || "",
        seller_email: "",
        description: "",
        amount: "",
        currency: "INR",
        remarks: "",
        expected_completion_date: "",
      });
      load();
    } catch (err) {
      console.error("Create failed:", err);
    }
  }

async function submitDocUpload(e) {
  e.preventDefault();

  const trade = trades.find(t => t.id === docUpload.tradeId);
  if (!trade) return;

  // SELLER UPLOAD
  if (me.role === "corp") {
    if (trade.status === "seller_confirmed") {
      await api.put(`/trades/${trade.id}/status`, null, {
        params: {
          new_status: "documents_uploaded",
          remarks: `Seller uploaded ${docUpload.docType}`,
        },
      });
    }
    setDocUpload({ tradeId: null, docType: "", file: null });
    load();
    return;
  }

  // BANK UPLOAD (AFTER APPROVAL)
  if (me.role === "bank") {
    if (!trade.bank_id) return;

    // first LC upload → set status once
    if (trade.status === "bank_approved") {
      await api.put(`/trades/${trade.id}/status`, null, {
        params: {
          new_status: "bank_documents_uploaded",
          remarks: "Bank uploaded LC",
        },
      });
    }

    setDocUpload({ tradeId: null, docType: "", file: null });
    load();
    return;
  }

  /* ================= BANK UPLOAD ================= */
  if (me?.role === "bank") {
    // Bank uploads LC or internal docs
    // ❌ DO NOT touch trade status
    alert("Bank document uploaded. Trade status not changed.");

    setDocUpload({ tradeId: null, docType: "LC", file: null });
    return; // 🚨 STOP HERE
  }

  /* ================= SELLER UPLOAD ================= */
  if (me?.role !== "corp" || trade.status !== "seller_confirmed") {
    alert("Only seller can upload trade documents at this stage.");
    return;
  }

  try {
    await api.put(`/trades/${trade.id}/status`, null, {
      params: {
        new_status: "documents_uploaded",
        remarks: `Seller uploaded ${docUpload.docType}`,
      },
    });

    setDocUpload({ tradeId: null, docType: "Commercial Invoice", file: null });
    load();
  } catch (err) {
    alert("Document upload failed.");
  }
}

  async function assignBank(e) {
    e.preventDefault();
    await api.put(`/trades/${assign.tradeId}/assign-bank`, null, {
      params: { bank_email: assign.bankEmail },
    });
    setAssign({ tradeId: null, bankEmail: "" });
    load();
  }

  async function submitRemarkAction(e) {
    e.preventDefault();
    try {
      await api.put(`/trades/${remarkModal.tradeId}/status`, null, {
        params: {
          new_status: remarkModal.action,
          remarks: remarkModal.remarks,
        },
      });
      setRemarkModal({ tradeId: null, action: "", remarks: "" });
      load();
    } catch (err) {
      console.error("Action failed:", err);
    }
  }

  async function confirmExpectedDate(tradeId) {
    await api.patch(`/trades/${tradeId}/expected-date/confirm`, {});
    load();
  }

  if (!me) return <div style={loadingStyle}>Initializing Secure Terminal...</div>;

  return (
    <div style={appContainer}>
      
      {/* HEADER */}
      <div style={header}>
        <div>
          <h2 style={{ margin: 0, color: "#f8fafc" }}>Trade Finance Terminal</h2>
          <div style={userBadge}>
            <span style={onlineDot}></span>
            {me.email} <span style={{ opacity: 0.5 }}>({me.role.toUpperCase()})</span>
          </div>
        </div>
      </div>

      {/* DASHBOARD */}
      <div style={dashboardGrid}>
        <DashCard icon="📊" label="Total" value={statusCounts.total} color="#38bdf8" />
        <DashCard icon="🆕" label="Initiated" value={statusCounts.initiated || 0} color="#94a3b8" />
        <DashCard icon="🤝" label="Accepted" value={statusCounts.seller_confirmed || 0} color="#a855f7" />
        <DashCard icon="📄" label="Docs" value={statusCounts.documents_uploaded || 0} color="#fbbf24" />
        <DashCard icon="🏦"label="Bank Assigned" value={statusCounts.bank_assigned || 0} />
        <DashCard icon="🏦" label="Review" value={statusCounts.bank_reviewing || 0} color="#38bdf8" />
        <DashCard icon="✅" label="Approved" value={statusCounts.bank_approved || 0} color="#34d399" />
        <DashCard icon="📑"label="Bank Docs" value={statusCounts.bank_documents_uploaded || 0} />
        <DashCard icon="💸" label="Released" value={statusCounts.payment_released || 0} color="#22d3ee" />
        <DashCard icon="🏆" label="Success" value={statusCounts.completed || 0} color="#10b981" />
        <DashCard icon="⚠️" label="Exceptions" value={(statusCounts.rejected || 0) + (statusCounts.disputed || 0)} color="#f87171" />
      </div>

      {/* CREATE TRADE (Corp only) */}
      {isCorp() && (
        <div style={darkBox}>
          <h3 style={sectionTitle}>+ Initiate New Trade TRX</h3>
          <form onSubmit={createTrade}style={{display: "grid",gridTemplateColumns: "1.2fr 1.2fr 1.1fr 1.4fr 1.1fr 1.2fr",gap: "14px",alignItems: "center", }}>
            <div style={inputGroup}><label style={labelStyle}>BUYER</label><input style={inputDisabled} value={createForm.buyer_email} disabled /></div>
            <div style={inputGroup}><label style={labelStyle}>SELLER</label><input style={inputStyle} placeholder="seller email..." value={createForm.seller_email} onChange={(e) => setCreateForm({ ...createForm, seller_email: e.target.value })} required /></div>
            <div style={inputGroup}>
              <label style={labelStyle}>AMOUNT</label>
              <div style={{  display: "grid",gridTemplateColumns: "2fr 1fr",gap: "8px",alignItems: "center", }}>
                <input style={{ ...inputStyle, flex: 2 }} type="number" placeholder="0.00" value={createForm.amount} onChange={(e) => setCreateForm({ ...createForm, amount: e.target.value })} required />
                <select style={{ ...inputStyle, flex: 1 }} value={createForm.currency} onChange={(e) => setCreateForm({ ...createForm, currency: e.target.value })}>
                  <option value="INR">INR</option>
                  <option value="USD">USD</option>
                  <option value="EUR">EUR</option>
                </select>
              </div>
            </div>
            <div style={inputGroup}><label style={labelStyle}>DESC.</label><input style={inputStyle} placeholder="Nature of goods..." value={createForm.description} onChange={(e) => setCreateForm({ ...createForm, description: e.target.value })} required /></div>
            <div style={inputGroup}><label style={labelStyle}>DUE DATE</label><input style={inputStyle} type="date" value={createForm.expected_completion_date} onChange={(e) => setCreateForm({ ...createForm, expected_completion_date: e.target.value })} required /></div>
           <button type="submit"style={{background: "#38bdf8",color: "#020617",border: "none",height: "44px",borderRadius: "10px",fontWeight: "bold",cursor: "pointer",fontSize: "13px",alignSelf: "end", }}>ORDER TRADE</button>
          </form>
        </div>
      )}

      {/* REGISTRY */}
      <h3 style={sectionTitle}>Active Registry (Audit history on click)</h3>
      {filteredTrades.map((t) => (
        <div key={t.id} style={wideCard} onClick={() => setSelectedTrade(t)}>
        {/* 🔥 ADDED: RAW TRADE ID */}
          <div style={cardCol}><span style={labelMuted}>TRADE ID</span> <span style={valBold}>{t.id}</span></div>
          <div style={cardCol}><span style={labelMuted}>TRADE NUMBER</span><span style={valBold}>{formatTradeNo(t)}</span></div>
          <div style={cardCol}><span style={labelMuted}>TYPE OF GOODS</span><span style={valBold}>{t.description || "—"}</span></div>
          <div style={cardCol}><span style={labelMuted}>ROLE ID</span><div style={valSmall}>{isBuyer(t) ? `SELLER ID: ${t.seller_id}` : `BUYER ID: ${t.buyer_id}`}</div></div>
          <div style={cardCol}><span style={labelMuted}>AMOUNT</span><span style={valBold}>{t.currency} {Number(t.amount).toLocaleString()}</span></div>
          <div style={cardCol}><span style={labelMuted}>STATUS</span><StatusBadge status={t.status} /></div>
          <div style={actionCol} onClick={(e) => e.stopPropagation()}>
{isSeller(t) && t.status === "initiated" && (
  <div style={btnGroup}>
    <button
      style={successBtn}
      onClick={() =>
        setRemarkModal({ tradeId: t.id, action: "seller_confirmed", remarks: "" })
      }
    >
      ACCEPT
    </button>
    <button
      style={dangerBtn}
      onClick={() =>
        setRemarkModal({ tradeId: t.id, action: "rejected", remarks: "" })
      }
    >
      REJECT
    </button>
  </div>
)}

{isSeller(t) && t.status === "seller_confirmed" && (
  <button
    style={actionBtn}
    onClick={() =>
      setDocUpload({ tradeId: t.id, docType: "Commercial Invoice", file: null })
    }
  >
    📤 UPLOAD DOCUMENTS
  </button>
)}

{isAdmin() && !t.bank_id && t.status === "documents_uploaded" && (
  <button
    style={actionBtn}
    onClick={() => setAssign({ tradeId: t.id, bankEmail: "" })}
  >
    ASSIGN BANK
  </button>
)}

{/* 🔥 FIXED: bank_assigned → START REVIEW */}
{isAssignedBank(t) && t.status === "bank_assigned" && (
  <button
    style={actionBtn}
    onClick={() =>
      setRemarkModal({ tradeId: t.id, action: "bank_reviewing", remarks: "" })
    }
  >
    START REVIEW
  </button>
)}

{isAssignedBank(t) && t.status === "bank_reviewing" && (
  <div style={btnGroup}>
    <button
      style={successBtn}
      onClick={() =>
        setRemarkModal({ tradeId: t.id, action: "bank_approved", remarks: "" })
      }
    >
      APPROVE
    </button>
    <button
      style={dangerBtn}
      onClick={() =>
        setRemarkModal({ tradeId: t.id, action: "rejected", remarks: "" })
      }
    >
      REJECT
    </button>
  </div>
)}

{/* BANK: UPLOAD LC (AFTER APPROVAL) */}
{isAssignedBank(t) &&
  (t.status === "bank_approved" ||
   t.status === "bank_documents_uploaded") && (
    <button
      style={actionBtn}
      onClick={() =>
        setDocUpload({
          tradeId: t.id,
          docType: "Letter of Credit (LC)",
          file: null,
        })
      }
    >
      📎 UPLOAD LC
    </button>
)}

{/* BANK: RELEASE FUNDS (AFTER APPROVAL OR LC UPLOAD) */}
{isAssignedBank(t) &&
  (t.status === "bank_approved" ||
   t.status === "bank_documents_uploaded") && (
    <button
      style={actionBtn}
      onClick={() =>
        setRemarkModal({
          tradeId: t.id,
          action: "payment_released",
          remarks: "",
        })
      }
    >
      💸 RELEASE FUNDS
    </button>
)}
            {(isBuyer(t) || isSeller(t)) && t.status === "payment_released" && (
              <button style={successBtn} onClick={() => setRemarkModal({ tradeId: t.id, action: "completed", remarks: "" })}>COMPLETE</button>
            )}
          </div>
        </div>
      ))}

      {/* TRACKER MODAL WITH TIMESTAMPS */}
      {selectedTrade && (
        <div style={modalOverlay} onClick={() => setSelectedTrade(null)}>
          <div style={modalContent} onClick={e => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 20 }}>
              <h3 style={{ margin: 0, color: "#38bdf8" }}>Life-Cycle: {formatTradeNo(selectedTrade)}</h3>
              <button style={closeBtn} onClick={() => setSelectedTrade(null)}>&times;</button>
            </div>
             <h3 style={{ color: "#38bdf8", marginBottom: 8 }}>
              {formatTradeNo(selectedTrade)}
            </h3>

            {/* 🔥 ADDED */}
            <div style={{ fontSize: 12, color: "#94a3b8", marginBottom: 20 }}>
              Trade ID: {selectedTrade.id}
            </div>
            <div style={trackerContainer}>
              {workflowStages.map((stage, index) => {
                const currentIdx = workflowStages.findIndex(s => s.key === selectedTrade.status);
                const isCompleted = currentIdx >= index;
                const isFailed = (selectedTrade.status === "rejected" || selectedTrade.status === "disputed") && index === currentIdx;
                // Display time if completed
                const timeStr = isCompleted ? formatTime(selectedTrade.updated_at) : null;

                return (
                  <div key={stage.key} style={trackerStep}>
                    <div style={trackerLeft}>
                      <div style={{ ...trackerCircle, backgroundColor: isFailed ? "#f87171" : isCompleted ? "#34d399" : "#1e293b" }}>
                        {isCompleted && !isFailed && "✓"}{isFailed && "!"}
                      </div>
                      {index < workflowStages.length - 1 && <div style={{ ...trackerLine, backgroundColor: currentIdx > index ? "#34d399" : "#1e293b" }} />}
                    </div>
                    <div style={trackerRight}>
                      <div style={{ ...trackerLabel, color: isFailed ? "#f87171" : isCompleted ? "#f8fafc" : "#475569" }}>{stage.label}</div>
                      <div style={trackerSubLabel}>
                        {isCompleted ? (index === currentIdx ? `Current - ${timeStr || 'Active'}` : `Finished - ${timeStr}`) : "Pending Process"}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* DOCUMENT UPLOAD MODAL */}
      {docUpload.tradeId &&
  ((me?.role === "corp") || (me?.role === "bank")) && (
    <div style={modalOverlay}>

          <form onSubmit={submitDocUpload} style={modalContent}>
            <h3>Submit Trade Docs: {formatTradeNo(trades.find(t => t.id === docUpload.tradeId))}</h3>
            <div style={{ marginBottom: 15 }}>
              <label style={labelStyle}>DOC CATEGORY</label>
              <select style={inputStyle} value={docUpload.docType} onChange={e => setDocUpload({...docUpload, docType: e.target.value})}>
                <option>Commercial Invoice</option>
                <option>Bill of Lading</option>
                <option>Packing List</option>
                <option>Letter Of credit</option>
              </select>
            </div>
            <div style={{ marginBottom: 20 }}><label style={labelStyle}>SELECT FILE</label><input type="file" style={{ color: "#94a3b8", fontSize: 13 }} required /></div>
            <div style={btnGroup}>
              <button style={primaryBtn}>UPLOAD & FINALISE</button>
              <button type="button" style={outlineBtn} onClick={() => setDocUpload({ tradeId: null, docType: "Commercial Invoice", file: null })}>CANCEL</button>
            </div>
          </form>
        </div>
      )}

      {/* ACTION MODALS (Remark/Assign) */}
      {remarkModal.tradeId && (
        <div style={modalOverlay}>
          <form onSubmit={submitRemarkAction} style={modalContent}>
            <h3 style={{ textTransform: 'uppercase', fontSize: 14 }}>ACTION: {remarkModal.action.replace("_", " ")}</h3>
            <textarea style={textareaStyle} placeholder="Enter audit remarks..." onChange={e => setRemarkModal({...remarkModal, remarks: e.target.value})} required />
            <div style={btnGroup}><button style={primaryBtn}>SUBMIT</button><button type="button" style={outlineBtn} onClick={() => setRemarkModal({tradeId: null})}>CANCEL</button></div>
          </form>
        </div>
      )}
      {assign.tradeId && (
        <div style={modalOverlay}>
          <form onSubmit={assignBank} style={modalContent}>
            <h3>Identify Clearing Bank</h3>
            <input style={inputStyle} placeholder="Bank Email" value={assign.bankEmail} onChange={e => setAssign({...assign, bankEmail: e.target.value})} required />
            <div style={btnGroup}><button style={primaryBtn}>ASSIGN</button><button type="button" style={outlineBtn} onClick={() => setAssign({tradeId: null})}>CANCEL</button></div>
          </form>
        </div>
      )}
    </div>
  );
}

/* --- ATOMIC COMPONENTS --- */
function DashCard({ icon, label, value, color }) {
  return (
    <div style={{ ...cardBase, borderTop: `2px solid ${color}` }}>
      <div style={{ fontSize: 20, marginBottom: 4 }}>{icon}</div>
      <div style={dashLabel}>{label}</div>
      <div style={{ fontSize: 22, fontWeight: "bold", color: "#f8fafc" }}>{value}</div>
    </div>
  );
}

function StatusBadge({ status }) {
  const c = status === 'completed' ? { bg: '#064e3b', text: '#34d399' } : status === 'rejected' ? { bg: '#450a0a', text: '#f87171' } : { bg: '#1e293b', text: '#38bdf8' };
  return <span style={{ backgroundColor: c.bg, color: c.text, padding: '2px 8px', borderRadius: '4px', fontSize: 11, fontWeight: 'bold', textTransform: 'uppercase' }}>{status.replace("_", " ")}</span>;
}

/* --- STYLES --- */
const appContainer = {backgroundColor: "#AFCBD5",minHeight: "100vh",padding: "24px",color: "#e5e7eb",fontFamily: "Inter, sans-serif"};
const loadingStyle = { height: "100vh", display: "flex", justifyContent: "center", alignItems: "center", color: "#38bdf8", background: "#020617" };
const header = { borderBottom: "1px solid #1e293b", paddingBottom: "20px", marginBottom: "32px", display: "flex", justifyContent: "space-between", alignItems: "center" };
const userBadge = { background: "#0f172a", border: "1px solid #1e293b", padding: "6px 12px", borderRadius: "6px", fontSize: 12, display: "flex", alignItems: "center" };
const onlineDot = { height: 8, width: 8, background: "#22c55e", borderRadius: "50%", marginRight: 8 };
const dashboardGrid = { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(100px, 1fr))", gap: "10px", marginBottom: "32px" };
const cardBase = { background: "#0f172a", padding: "16px", borderRadius: "8px", border: "1px solid #1e293b", textAlign: "center" };
const dashLabel = { fontSize: 10, color: "#475569", fontWeight: "bold", textTransform: "uppercase" };
const darkBox = { background: "#0f172a", border: "1px solid #1e293b", borderRadius: "12px", padding: "24px", marginBottom: "32px" };
const sectionTitle = { fontSize: 13, fontWeight: "bold", textTransform: "uppercase", color: "#475569", letterSpacing: "1px", marginBottom: "16px" };
const wideCard = {
  display: "grid",
  gridTemplateColumns: "0.6fr 1.4fr 1.8fr 1fr 1.2fr 1.4fr 1.2fr",
  alignItems: "center",          // 🔥 THIS fixes vertical alignment
  background: "#0f172a",
  border: "1px solid #1e293b",
  borderRadius: "14px",
  padding: "18px 24px",
  marginBottom: "14px",
  gap: "16px",
  cursor: "pointer",
};

const cell = {
  display: "flex",
  flexDirection: "column",
  justifyContent: "center",
  gap: "4px",
};
const actionCell = {
  display: "flex",
  justifyContent: "flex-end",
  alignItems: "center",
};
const completeBtn = {
  background: "#34d399",
  color: "#022c22",
  border: "none",
  padding: "10px 18px",
  borderRadius: "10px",
  fontWeight: "bold",
  fontSize: "12px",
  cursor: "pointer",
};

const cardCol = { display: "flex", flexDirection: "column", gap: "4px" };
const labelMuted = { fontSize: 9, color: "#475569", fontWeight: "bold" };
const valBold = { fontSize: 14, fontWeight: "bold", color: "#f8fafc" };
const valSmall = { fontSize: 11, color: "#94a3b8" };
const actionCol = { display: "flex", justifyContent: "flex-end", gap: "8px" };
const formGrid = { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "16px", alignItems: "end" };
const inputGroup = { display: "flex", flexDirection: "column", gap: "6px" };
const labelStyle = { fontSize: 10, fontWeight: "bold", color: "#475569" };
const inputStyle = { background: "#020617", border: "1px solid #334155", color: "#f8fafc", padding: "10px", borderRadius: "6px", fontSize: 14 };
const inputDisabled = { ...inputStyle, opacity: 0.5 };
const textareaStyle = { ...inputStyle, minHeight: "80px", width: "100%", boxSizing: "border-box" };
const primaryBtn = { background: "#38bdf8", color: "#020617", border: "none", padding: "10px 16px", borderRadius: "6px", fontWeight: "bold", cursor: "pointer", fontSize: 13 };
const successBtn = { ...primaryBtn, background: "#34d399", padding: "8px 15px" };
const dangerBtn = { ...primaryBtn, background: "#f87171", padding: "8px 15px" };
const actionBtn = { ...primaryBtn, background: "#1e293b", color: "#38bdf8", border: "1px solid #334155", padding: "8px 15px" };
const outlineBtn = { background: "transparent", color: "#94a3b8", border: "1px solid #334155", padding: "10px 16px", borderRadius: "6px", cursor: "pointer", fontSize: 13 };
const closeBtn = { background: "transparent", border: "none", color: "#475569", fontSize: 24, cursor: "pointer" };
const btnGroup = { display: "flex", gap: "8px" };
const modalOverlay = { position: "fixed", top: 0, left: 0, width: "100%", height: "100%", background: "rgba(0,0,0,0.85)", display: "flex", justifyContent: "center", alignItems: "center", zIndex: 100 };
const modalContent = { background: "#0f172a", padding: "30px", borderRadius: "16px", border: "1px solid #38bdf8", width: "90%", maxWidth: "450px" };
const trackerContainer = { display: 'flex', flexDirection: 'column', padding: '10px 0' };
const trackerStep = { display: 'flex', gap: '20px' };
const trackerLeft = { display: 'flex', flexDirection: 'column', alignItems: 'center' };
const trackerCircle = { width: '24px', height: '24px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '12px', fontWeight: 'bold', color: '#020617', zIndex: 2 };
const trackerLine = { width: '2px', height: '30px', margin: '2px 0' };
const trackerRight = { paddingBottom: '20px' };
const trackerLabel = { fontSize: '14px', fontWeight: 'bold', marginBottom: '2px' };
const trackerSubLabel = { fontSize: '11px', color: '#64748b' };