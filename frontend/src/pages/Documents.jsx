import React, { useEffect, useState } from "react";
import api from "../api/axios";

export default function Documents() {
  const [docs, setDocs] = useState([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedDoc, setSelectedDoc] = useState(null);

  const [file, setFile] = useState(null);
  const [docType, setDocType] = useState("");
  const [tradeId, setTradeId] = useState("");

  const [hashVerify, setHashVerify] = useState("");
  const [verifyResult, setVerifyResult] = useState(null);

  const [loading, setLoading] = useState(false);

  const [updateFile, setUpdateFile] = useState(null);
  const [updating, setUpdating] = useState(false);

  const [beforeHash, setBeforeHash] = useState(null);
  const [afterHash, setAfterHash] = useState(null);

  /* ================= FETCH DOCUMENTS ================= */
  const fetchDocs = async () => {
    try {
      const res = await api.get("/documents/all");
      setDocs(res.data);
    } catch {
      alert("Failed to load documents");
    }
  };

  useEffect(() => {
    fetchDocs();
  }, []);

  /* ================= HASH UTILITY ================= */
  const calculateHash = async (file) => {
    const buffer = await file.arrayBuffer();
    const hashBuffer = await crypto.subtle.digest("SHA-256", buffer);
    return Array.from(new Uint8Array(hashBuffer))
      .map((b) => b.toString(16).padStart(2, "0"))
      .join("");
  };

  /* ================= UPLOAD DOCUMENT ================= */
  const uploadDocument = async () => {
    if (!file || !docType || !tradeId) {
      alert("Trade ID, Document Type, and File are REQUIRED");
      return;
    }

    try {
      setLoading(true);

      const hash = await calculateHash(file);
      if (docs.some((d) => d.hash === hash)) {
        alert("Duplicate document detected");
        return;
      }

      const form = new FormData();
      form.append("doc_type", docType);
      form.append("file", file);
      form.append("trade_id", tradeId);

      await api.post("/documents/upload", form);

      setFile(null);
      setDocType("");
      setTradeId("");
      fetchDocs();
    } catch {
      alert("Upload failed");
    } finally {
      setLoading(false);
    }
  };

  /* ================= UPDATE DOCUMENT + LEDGER ================= */
  const updateDocument = async () => {
    if (!selectedDoc || !updateFile) return;

    try {
      setUpdating(true);

      const oldHash = selectedDoc.hash;
      const newHash = await calculateHash(updateFile);

      setBeforeHash(oldHash);
      setAfterHash(newHash);

      const form = new FormData();
      form.append("doc_id", selectedDoc.doc_id);
      form.append("file", updateFile);

      await api.put("/documents/update", form);

      await api.post("/ledger", {
        event_type: "MODIFIED",
        doc_id: selectedDoc.doc_id,
        description: "Document updated",
        hash_before: oldHash,
        hash_after: newHash,
        event_metadata: {
          trade_id: selectedDoc.trade_id,
          doc_type: selectedDoc.doc_type,
        },
      });

      setUpdateFile(null);
      fetchDocs();
    } catch {
      alert("Update failed");
    } finally {
      setUpdating(false);
    }
  };

  /* ================= VERIFY DOCUMENT + LEDGER ================= */
  const verifyDocument = async () => {
    if (!hashVerify) return;

    try {
      const res = await api.get(`/documents/verify/${hashVerify}`);
      setVerifyResult(res.data);

      if (res.data.verified && selectedDoc) {
        await api.post("/ledger", {
          event_type: "VERIFIED",
          doc_id: selectedDoc.doc_id,
          description: "Document hash verified",
          hash_before: selectedDoc.hash,
          hash_after: selectedDoc.hash,
          event_metadata: {
            trade_id: selectedDoc.trade_id,
            doc_type: selectedDoc.doc_type,
          },
        });
      }
    } catch {
      setVerifyResult({ verified: false });
    }
  };

  /* ================= FILTER ================= */
  const filteredDocs = docs.filter((d) =>
    `${d.doc_id} ${d.doc_type} ${d.file_name}`
      .toLowerCase()
      .includes(searchTerm.toLowerCase())
  );

  return (
    <div style={containerStyle}>
      {/* HEADER */}
      <header style={headerStyle}>
        <h2 style={{ fontWeight: 800, color: "#043344" }}>Documents</h2>
        <input
          style={searchBoxStyle}
          placeholder="Search documents..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </header>

      {/* VERIFY */}
      <div style={verifyBox}>
        <input
          style={inputStyle}
          placeholder="Paste SHA-256 hash to verify"
          value={hashVerify}
          onChange={(e) => setHashVerify(e.target.value)}
        />
        <button onClick={verifyDocument} style={primaryBtnStyle}>
          Verify
        </button>

        {verifyResult && (
          <div
            style={{
              marginTop: 8,
              fontWeight: 700,
              color: verifyResult.verified ? "#065F46" : "#991B1B",
            }}
          >
            {verifyResult.verified
              ? "✔ Document integrity verified"
              : "✖ Hash verification failed"}
          </div>
        )}
      </div>

      {/* UPLOAD */}
      <div style={uploadCard}>
        <h3 style={sectionTitleStyle}>Upload Document</h3>

        <select
          style={inputStyle}
          value={docType}
          onChange={(e) => setDocType(e.target.value)}
        >
          <option value="">Select Document Type</option>
          <option value="PO">Purchase Order (PO)</option>
          <option value="INVOICE">Invoice</option>
          <option value="LC">Letter of Credit (LC)</option>
          <option value="LOC">Letter of Credit (LOC)</option>
          <option value="BOL">Bill of Lading</option>
          <option value="PACKING_LIST">Packing List</option>
          <option value="INSURANCE">Insurance Certificate</option>
          <option value="COO">Certificate of Origin</option>
          <option value="AWB">Air Waybill</option>
          <option value="CUSTOMS">Customs Document</option>
          <option value="OTHER">Other</option>
        </select>

        <input
          style={inputStyle}
          placeholder="Trade ID (REQUIRED)"
          value={tradeId}
          onChange={(e) => setTradeId(e.target.value)}
        />

        <input type="file" onChange={(e) => setFile(e.target.files[0])} />

        <button
          disabled={loading}
          onClick={uploadDocument}
          style={primaryBtnStyle}
        >
          {loading ? "Uploading..." : "Upload"}
        </button>
      </div>

      {/* DOCUMENT LIST */}
      <div style={listCard}>
        <div style={docHeaderRow}>
          <span>ID</span>
          <span>TYPE</span>
          <span>FILE NAME</span>
        </div>

        {filteredDocs.map((d) => (
          <div
            key={d.doc_id}
            style={docRowStyle}
            onClick={() => {
              setSelectedDoc(d);
              setBeforeHash(null);
              setAfterHash(null);
            }}
          >
            <span style={mono}>{d.doc_id}</span>
            <span style={typePill}>{d.doc_type}</span>
            <span style={fileName}>{d.file_name}</span>
          </div>
        ))}
      </div>

      {/* DETAILS MODAL */}
      {selectedDoc && (
        <div style={modalOverlay} onClick={() => setSelectedDoc(null)}>
          <div style={modalContent} onClick={(e) => e.stopPropagation()}>
            <h3 style={{ color: "#0369A1", fontWeight: 800 }}>
              Document Details
            </h3>

            <p><strong>Document ID:</strong> {selectedDoc.doc_id}</p>
            <p><strong>Trade ID:</strong> {selectedDoc.trade_id}</p>
            <p><strong>Type:</strong> {selectedDoc.doc_type}</p>
            <p><strong>File:</strong> {selectedDoc.file_name}</p>

            <div style={hashBox}>{selectedDoc.hash}</div>

            {beforeHash && <div style={hashBox}>{beforeHash}</div>}
            {afterHash && (
              <div style={{ ...hashBox, color: "#047857" }}>{afterHash}</div>
            )}

            <input
              type="file"
              onChange={(e) => setUpdateFile(e.target.files[0])}
            />

            <button
              onClick={updateDocument}
              disabled={updating}
              style={primaryBtnStyle}
            >
              {updating ? "Updating..." : "Update Document"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

/* ================= STYLES ================= */

const containerStyle = {
  background: "#81D8D0",
  minHeight: "100vh",
  padding: "40px",
  color: "#043344",
};

const headerStyle = {
  display: "flex",
  justifyContent: "space-between",
  marginBottom: "20px",
};

const verifyBox = {
  background: "#D1FAF5",
  border: "1px solid #2DD4BF",
  padding: "16px",
  borderRadius: "14px",
  marginBottom: "24px",
};

const uploadCard = {
  background: "#ECFEFF",
  border: "1px solid #38BDF8",
  padding: "20px",
  borderRadius: "18px",
  marginBottom: "24px",
};

const listCard = {
  background: "#F0FDFA",
  border: "1px solid #5EEAD4",
  borderRadius: "18px",
  overflow: "hidden",
};

const docHeaderRow = {
  display: "grid",
  gridTemplateColumns: "100px 160px 1fr",
  padding: "12px 16px",
  fontSize: "11px",
  fontWeight: 900,
  letterSpacing: "0.15em",
  color: "#0F766E",
  background: "#CCFBF1",
  borderBottom: "1px solid #2DD4BF",
};

const docRowStyle = {
  display: "grid",
  gridTemplateColumns: "100px 160px 1fr",
  alignItems: "center",
  padding: "14px 16px",
  borderBottom: "1px solid #99F6E4",
  cursor: "pointer",
};

const mono = { fontFamily: "monospace" };

const typePill = {
  background: "#0EA5A4",
  color: "#FFFFFF",
  padding: "4px 10px",
  borderRadius: "999px",
  fontSize: "11px",
  fontWeight: 900,
  width: "fit-content",
};

const fileName = {
  whiteSpace: "nowrap",
  overflow: "hidden",
  textOverflow: "ellipsis",
};

const primaryBtnStyle = {
  background: "linear-gradient(135deg, #0EA5A4, #0284C7)",
  color: "#FFFFFF",
  borderRadius: "10px",
  padding: "10px 18px",
  fontWeight: 800,
  border: "none",
  marginTop: "10px",
};

const inputStyle = {
  width: "100%",
  background: "#F8FAFC",
  border: "1px solid #38BDF8",
  padding: "10px",
  borderRadius: "10px",
  color: "#043344",
  marginBottom: "10px",
  fontWeight: 600,
};

const searchBoxStyle = {
  background: "#F8FAFC",
  border: "1px solid #38BDF8",
  borderRadius: "10px",
  padding: "8px 12px",
  color: "#043344",
  width: "300px",
  fontWeight: 600,
};

const modalOverlay = {
  position: "fixed",
  inset: 0,
  background: "rgba(3, 105, 161, 0.35)",
  display: "flex",
  justifyContent: "center",
  alignItems: "center",
};

const modalContent = {
  background: "#E0F2FE",
  padding: "24px",
  borderRadius: "18px",
  border: "1px solid #38BDF8",
  width: "90%",
  maxWidth: "520px",
};

const hashBox = {
  background: "#F8FAFC",
  border: "1px solid #CBD5E1",
  padding: "12px",
  borderRadius: "10px",
  fontFamily: "monospace",
  marginTop: "8px",
};

const sectionTitleStyle = {
  fontSize: "12px",
  fontWeight: 900,
  color: "#0369A1",
};
