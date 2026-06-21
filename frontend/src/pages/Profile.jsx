import React, { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import api from "../api/axios";

export default function Profile() {
  const { user } = useAuth(); // Data from auth_routes.py (/me)
  const [riskData, setRiskData] = useState(null);
  const [loadingRisk, setLoadingRisk] = useState(true);

  useEffect(() => {
    // Hits the GET /risk/me endpoint in risk_routes.py
    api.get("/risk/me")
      .then((res) => {
        setRiskData(res.data);
        setLoadingRisk(false);
      })
      .catch((err) => {
        console.error("Risk score not found:", err);
        setLoadingRisk(false);
      });
  }, []);

  return (
    <div className="min-h-screen bg-gray-900 p-8 text-white">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">User Profile</h1>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Left Column: User Identity Card */}
          <div className="md:col-span-2 bg-gray-800 border border-gray-700 rounded-2xl p-8 shadow-2xl">
            <div className="flex items-center gap-6 mb-8">
              <div className="h-20 w-20 bg-blue-600 rounded-full flex items-center justify-center text-3xl font-bold">
                {user?.name?.charAt(0).toUpperCase()}
              </div>
              <div>
                <h2 className="text-2xl font-bold text-white">{user?.name}</h2>
                <p className="text-blue-400 font-mono text-sm">{user?.email}</p>
              </div>
            </div>

            <div className="space-y-6">
              <div className="flex justify-between border-b border-gray-700 pb-4">
                <span className="text-gray-500 uppercase text-xs font-bold tracking-widest">Designated Role</span>
                <span className="bg-gray-900 px-3 py-1 rounded text-sm font-mono text-gray-300">
                  {user?.role?.toUpperCase()}
                </span>
              </div>

              <div className="flex justify-between border-b border-gray-700 pb-4">
                <span className="text-gray-500 uppercase text-xs font-bold tracking-widest">Organization</span>
                <span className="text-gray-300">{user?.org_name || "Platform Governance"}</span>
              </div>

              <div className="flex justify-between border-b border-gray-700 pb-4">
                <span className="text-gray-500 uppercase text-xs font-bold tracking-widest">Account ID</span>
                <span className="text-gray-500 font-mono text-sm">{user?.id}</span>
              </div>
            </div>
          </div>

          {/* Right Column: Risk & Security Status */}
          <div className="bg-gray-800 border border-gray-700 rounded-2xl p-8 shadow-2xl flex flex-col justify-between">
            <div>
              <h3 className="text-gray-400 uppercase text-xs font-bold tracking-widest mb-4">Security Assessment</h3>
              {loadingRisk ? (
                <div className="animate-pulse text-gray-600">Calculating...</div>
              ) : riskData ? (
                <div className="text-center">
                  <div 
                    className="text-5xl font-black mb-2" 
                    style={{ color: riskData.risk_color || "#3b82f6" }}
                  >
                    {riskData.score}
                  </div>
                  <div 
                    className="text-xs font-bold uppercase py-1 px-4 rounded-full inline-block mb-4"
                    style={{ backgroundColor: `${riskData.risk_color}20`, color: riskData.risk_color }}
                  >
                    {riskData.risk_level}
                  </div>
                  <p className="text-xs text-gray-500 italic">"{riskData.rationale}"</p>
                </div>
              ) : (
                <p className="text-xs text-gray-500">No risk assessment generated yet.</p>
              )}
            </div>

            <button 
              onClick={() => window.location.reload()}
              className="mt-6 w-full py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-xs font-bold transition-all"
            >
              REFRESH DATA
            </button>
          </div>
        </div>

        {/* Bottom Section: Security Notice */}
        <div className="mt-8 p-4 bg-blue-900/10 border border-blue-500/20 rounded-lg">
          <p className="text-xs text-blue-400 text-center">
            This profile is authenticated via the Trade Finance Ledger. Any changes to core identity must be approved by the System Administrator.
          </p>
        </div>
      </div>
    </div>
  );
}