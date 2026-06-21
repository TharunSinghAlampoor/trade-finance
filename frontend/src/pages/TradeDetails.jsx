import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { tradeService } from "../api/tradeApi";
import { 
  ArrowLeft, Clock, CheckCircle, Shield, 
  AlertCircle, ChevronRight, Landmark 
} from "lucide-react";

export default function TradeDetails() {
  const { tradeId } = useParams();
  const navigate = useNavigate();
  const [trade, setTrade] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Safely get user from localStorage
  const user = JSON.parse(localStorage.getItem("user") || "{}");

  // Backend STATUS_FLOW logic
  const STATUS_FLOW = {
    initiated: { seller_confirmed: ["corp"] },
    seller_confirmed: { documents_uploaded: ["corp"] },
    documents_uploaded: { bank_reviewing: ["bank"] },
    bank_reviewing: { bank_approved: ["bank"] },
    bank_approved: { payment_released: ["bank"] },
    payment_released: { completed: ["corp"] },
  };

  const loadTradeData = async () => {
    try {
      setLoading(true);
      const res = await tradeService.getTrade(tradeId);
      setTrade(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || "Trade not found or unauthorized access.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (tradeId) loadTradeData();
  }, [tradeId]);

  const handleStatusUpdate = async (nextStatus) => {
    const remarks = prompt(`Enter remarks for advancing to ${nextStatus.replace("_", " ")}:`);
    if (remarks === null) return;

    try {
      await tradeService.updateStatus(trade.id, nextStatus, remarks);
      loadTradeData(); // Refresh to see changes
    } catch (err) {
      alert(err.response?.data?.detail || "Action failed.");
    }
  };

  // Guard for Loading and Errors to prevent White Screen
  if (loading) return <div className="p-10 text-center animate-pulse">Fetching Secure Trade Data...</div>;
  if (error) return <div className="p-10 text-red-600 font-bold text-center">{error}</div>;
  if (!trade) return null;

  const currentActions = STATUS_FLOW[trade.status] || {};

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-6">
      <button onClick={() => navigate("/trades")} className="flex items-center text-slate-500 hover:text-blue-600 font-medium gap-2">
        <ArrowLeft size={18} /> Back to Ledger
      </button>

      {/* Main Trade Card */}
      <div className="bg-white rounded-2xl shadow-xl overflow-hidden border border-slate-100">
        <div className="bg-slate-900 p-6 text-white flex justify-between items-center">
          <div>
            <span className="text-blue-400 text-xs font-bold uppercase tracking-widest">{trade.trade_num}</span>
            <h1 className="text-2xl font-bold">{trade.description}</h1>
          </div>
          <div className="text-right">
            <p className="text-2xl font-black">{trade.currency} {trade.amount?.toLocaleString()}</p>
            <span className="bg-blue-600 px-3 py-1 rounded-full text-[10px] font-bold uppercase">
              {trade.status.replace("_", " ")}
            </span>
          </div>
        </div>

        {/* Action Command Center */}
        <div className="p-6 bg-slate-50 border-b flex flex-wrap gap-4 items-center">
          <Shield size={20} className="text-slate-400" />
          <span className="text-sm font-bold text-slate-500 uppercase mr-4">Required Actions:</span>
          
          {Object.entries(currentActions).length === 0 && (
            <span className="text-sm italic text-slate-400">No pending actions for current status.</span>
          )}

          {Object.entries(currentActions).map(([nextStatus, roles]) => (
            roles.includes(user.role) && (
              <button
                key={nextStatus}
                onClick={() => handleStatusUpdate(nextStatus)}
                className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-xl font-bold text-sm flex items-center gap-2 shadow-lg transition-transform active:scale-95"
              >
                Advance to {nextStatus.replace("_", " ")} <ChevronRight size={16} />
              </button>
            )
          ))}

          {/* Seller Confirmation Date Logic */}
          {user.id === trade.seller.id && trade.expected_completion_date && !trade.expected_date_confirmed && (
            <button 
              onClick={() => tradeService.confirmExpectedDate(trade.id).then(loadTradeData)}
              className="bg-green-600 text-white px-4 py-2 rounded-xl font-bold text-sm"
            >
              Confirm Expected Date
            </button>
          )}
        </div>

        {/* Audit Trail */}
        <div className="p-8">
          <h3 className="text-lg font-bold mb-6 flex items-center gap-2 text-slate-800">
            <Clock size={20} className="text-slate-400" /> Point-to-Point Audit History
          </h3>
          
          <div className="space-y-8">
            {trade.status_history.map((history, idx) => (
              <div key={idx} className="relative pl-8 border-l-2 border-slate-100 last:border-0 pb-2">
                <div className="absolute -left-[9px] top-0 w-4 h-4 rounded-full bg-blue-500 ring-4 ring-white shadow-sm" />
                <div className="flex justify-between items-start">
                  <div>
                    <p className="text-xs font-black uppercase text-blue-600 tracking-tighter">{history.status.replace("_", " ")}</p>
                    <p className="text-slate-700 font-medium mt-1">{history.remarks}</p>
                  </div>
                  <span className="text-[10px] font-mono text-slate-400 bg-slate-50 px-2 py-1 rounded">
                    {new Date(history.created_at).toLocaleString()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}