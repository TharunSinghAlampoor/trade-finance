import React, { useEffect, useState, useCallback } from "react";
import {
  User, Shield, Activity, RefreshCw,
  Server, Database, Wifi, AlertCircle
} from "lucide-react";
import api from "../api/axios";

/**
 * Institutional Audit Node Dashboard
 * Developed by: Tharun
 * All Rights Reserved © 2026
 */
export default function Dashboard() {
  const [me, setMe] = useState(null);
  const [trades, setTrades] = useState([]);
  const [risk, setRisk] = useState(null);
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadDashboard = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [meRes, tradesRes, riskRes, healthRes] = await Promise.all([
        api.get("/auth/me"),
        api.get("/trades"),
        api.get("/risk/me"),
        api.get("/health"),
      ]);

      setMe(meRes.data);
      setTrades(tradesRes.data || []);
      setRisk(riskRes.data || null);
      setHealth(healthRes.data || null);
    } catch (err) {
      console.error("Dashboard load failed", err);
      setError("Institutional Node Connection Failed. (Verify API status)");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  if (loading) return <div style={fullPageLoading}>Synchronising Audit Node...</div>;

  if (error || !me) {
    return (
      <div style={fullPageLoading}>
        <div style={{ textAlign: 'center', maxWidth: '450px' }}>
          <AlertCircle size={48} color="#ef4444" style={{ margin: '0 auto 16px' }} />
          <h2 style={{ color: '#ecfeff' }}>{error || "Profile data missing"}</h2>
          <button onClick={loadDashboard} style={refreshBtn}>Retry Handshake</button>
        </div>
      </div>
    );
  }

  const score = risk?.score ?? 0;
  const riskColor = score >= 80 ? "#22c55e" : score >= 50 ? "#eab308" : "#ef4444";
  const apiOnline = health?.status === "OK";
  const dbOnline = health?.database === "UP";

  return (
    <div style={layout}>
      <header style={header}>
        <div>
          <h1 style={title}>System Overview</h1>
          <p style={subtext}>
            Lead Auditor: <span style={{ color: '#73E6CB', fontWeight: '900' }}>Tharun</span>
          </p>
        </div>
        <div style={headerActions}>
          <div style={roleBadge}>{me?.role?.toUpperCase() || "ACCESS PENDING"}</div>
          <button onClick={loadDashboard} style={refreshBtn}>
            <RefreshCw size={14}/>
          </button>
        </div>
      </header>

      <div style={dashboardGrid}>
        <div style={sideCol}>
          <div style={card}>
            <div style={cardHeader}><User size={16}/> Profile Identity</div>
            <div style={profileDetail}>
              <label style={miniLabel}>Node UID</label>
              <div style={valText}>{me?.id || "---"}</div>
            </div>
            <div style={profileDetail}>
              <label style={miniLabel}>Registered Email</label>
              <div style={valText}>{me?.email || "---"}</div>
            </div>
            <div style={profileDetail}>
              <label style={miniLabel}>System Role</label>
              <div style={valText}>{me?.role || "---"}</div>
            </div>
          </div>
        </div>

        <div style={mainCol}>
          <div style={statsRow}>
            <div style={statCard}>
              <div style={cardHeader}><Activity size={16}/> Ledger Volume</div>
              <div style={hugeVal}>{trades?.length || 0}</div>
              <div style={miniLabel}>Canonical Trade Records</div>
            </div>

            <div style={statCard}>
              <div style={cardHeader}><Shield size={16}/> Risk Profile</div>
              <div style={{ ...hugeVal, color: riskColor }}>{score}%</div>
              <div style={{ ...riskTag, backgroundColor: `${riskColor}22`, color: riskColor }}>
                {score >= 80 ? 'STABLE' : 'EVALUATION REQUIRED'}
              </div>
            </div>
          </div>

          <div style={card}>
            <div style={cardHeader}><Server size={16}/> Infrastructure Telemetry</div>
            <div style={healthGrid}>
              <HealthStatus icon={<Wifi size={18}/>} label="Primary API" status={apiOnline ? "ONLINE" : "DOWN"} ok={apiOnline} />
              <HealthStatus icon={<Database size={18}/>} label="Database" status={health?.database || "UNKNOWN"} ok={dbOnline} />
              <HealthStatus icon={<AlertCircle size={18}/>} label="System Latency" status="< 24ms" ok />
            </div>
          </div>
        </div>
      </div>

      <footer style={copyrightFooter}>
        <div style={footerDivider}></div>
        <div style={footerContent}>
          <span>AuditCore Platform v2.4.0</span>
          <span>All Rights Reserved © 2026 Tharun</span>
          <span style={{ color: '#73E6CB', fontWeight: '900' }}>SECURE NODE</span>
        </div>
      </footer>
    </div>
  );
}

/* ================= ATOMIC COMPONENTS ================= */

function HealthStatus({ icon, label, status, ok }) {
  const color = ok ? "#22c55e" : "#ef4444";
  return (
    <div style={healthItem}>
      <div style={{ ...iconCircle, color, borderColor: `${color}55` }}>{icon}</div>
      <div>
        <div style={miniLabel}>{label}</div>
        <div style={{ fontSize: '14px', fontWeight: '800', color }}>
          {status} {ok && <span style={pulseDot}></span>}
        </div>
      </div>
    </div>
  );
}

/* ================= STYLES ================= */

const layout = {
  minHeight: "100vh",
  padding: "32px",
  display: "flex",
  flexDirection: "column",
  fontFamily: "'Inter', sans-serif",
  background: "linear-gradient(135deg, #020617 0%, #0f766e 45%, #73E6CB 100%)",
  color: "#ecfeff"
};

const header = { display: 'flex', justifyContent: 'space-between', marginBottom: '32px' };
const title = { fontSize: '26px', fontWeight: '900', color: "#ccfbf1" };
const subtext = { fontSize: '12px', color: '#5eead4' };
const headerActions = { display: 'flex', gap: '12px', alignItems: 'center' };

const roleBadge = {
  background: "linear-gradient(135deg, #14b8a6, #2dd4bf)",
  padding: '6px 14px',
  borderRadius: '999px',
  fontSize: '10px',
  fontWeight: '900',
  color: "#042f2e"
};

const refreshBtn = {
  background: "#022c22",
  border: "1px solid #2dd4bf",
  borderRadius: "8px",
  padding: "6px",
  color: "#5eead4",
  cursor: "pointer"
};

const dashboardGrid = { display: 'grid', gridTemplateColumns: '300px 1fr', gap: '24px', flex: 1 };
const sideCol = { display: 'flex', flexDirection: 'column', gap: '20px' };
const mainCol = { display: 'flex', flexDirection: 'column', gap: '20px' };

const card = {
  background: "#042f2e",
  border: "1px solid #14b8a6",
  borderRadius: "16px",
  padding: "24px",
  boxShadow: "0 10px 30px rgba(20,184,166,0.15)"
};

const statCard = {
  ...card,
  background: "linear-gradient(160deg, #042f2e, #134e4a)",
  border: "1px solid #2dd4bf"
};

const cardHeader = {
  display: 'flex',
  gap: '8px',
  fontSize: '11px',
  fontWeight: '900',
  textTransform: 'uppercase',
  marginBottom: '20px',
  color: "#67e8f9",
  letterSpacing: "0.08em"
};

const profileDetail = { marginBottom: '16px' };
const miniLabel = { fontSize: '10px', color: '#2dd4bf', fontWeight: '800' };
const valText = { fontSize: '14px', fontWeight: '700', color: "#ecfeff" };

const statsRow = { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' };
const hugeVal = { fontSize: '42px', fontWeight: '900' };
const riskTag = { fontSize: '10px', padding: '4px 8px', borderRadius: '4px', fontWeight: '900' };

const healthGrid = { display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px' };
const healthItem = { display: 'flex', gap: '12px', background: "#022c22", padding: '16px', borderRadius: '12px', border: '1px solid #14b8a6' };
const iconCircle = { width: 36, height: 36, borderRadius: 10, border: "1px solid", display: 'flex', alignItems: 'center', justifyContent: 'center' };

const pulseDot = { width: 6, height: 6, borderRadius: '50%', background: 'currentColor', marginLeft: 8 };
const fullPageLoading = { height: '100vh', display: 'flex', justifyContent: 'center', alignItems: 'center', background: "#020617", color: "#73E6CB" };

const copyrightFooter = { marginTop: 'auto', paddingTop: '40px' };
const footerDivider = { height: '1px', background: '#134e4a', marginBottom: '16px' };
const footerContent = { display: 'flex', justifyContent: 'space-between', fontSize: '11px', fontWeight: '700', color: '#5eead4' };
