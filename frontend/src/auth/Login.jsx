import { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { useNavigate, Link } from "react-router-dom";
import { 
  ShieldCheck, Lock, Mail, ChevronRight, 
  ShieldAlert, Globe, Landmark, Activity 
} from "lucide-react";

/**
 * Institutional Trade Finance Gateway v3.1
 * Developed by: Tharun // 2026
 * All Rights Reserved © 2026 Tharun
 */
export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setIsSubmitting(true);

    setTimeout(async () => {
      try {
        await login(email, password);
        navigate("/dashboard");
      } catch (err) {
        setError(err.response?.data?.detail || "Node connection rejected.");
        setIsSubmitting(false);
      }
    }, 1200);
  };

  return (
    <div className="min-h-screen relative flex items-center justify-center font-sans overflow-hidden bg-black">

      {/* ================= CINEMATIC BACKGROUND ================= */}
      <div 
        className="absolute inset-0 z-0 bg-cover bg-center bg-no-repeat scale-110 animate-bg-drift"
        style={{ 
          backgroundImage: `url('https://images.unsplash.com/photo-1518458028785-8fbcd101ebb9?auto=format&fit=crop&q=80&w=2070')`,
          filter: 'brightness(0.22) grayscale(0.45)'
        }}
      />

      {/* ================= LIGHT BLOOMS ================= */}
      <div className="absolute -top-40 -left-40 w-[600px] h-[600px] bg-indigo-600/30 blur-[160px] rounded-full animate-float-slow" />
      <div className="absolute bottom-0 right-0 w-[500px] h-[500px] bg-cyan-500/20 blur-[140px] rounded-full animate-float-reverse" />

      {/* ================= GRID + NOISE ================= */}
      <div className="absolute inset-0 z-10 opacity-10 bg-grid" />
      <div className="absolute inset-0 z-10 pointer-events-none bg-noise" />

      {/* ================= MAIN INTERFACE ================= */}
      <main className="relative z-20 w-full max-w-5xl flex flex-col md:flex-row p-4 animate-in fade-in zoom-in duration-1000">

        {/* ================= LEFT PANEL ================= */}
        <div className="flex-1 p-10 lg:p-16 bg-white/5 backdrop-blur-xl border border-white/10 rounded-t-[2.5rem] md:rounded-l-[2.5rem] md:rounded-t-none relative overflow-hidden">
          <div className="absolute inset-0 pointer-events-none border-glow" />

          <div className="flex items-center gap-4 mb-14">
            <div className="p-3 bg-indigo-600 rounded-2xl shadow-[0_0_40px_rgba(79,70,229,0.6)]">
              <Landmark size={28} className="text-white" />
            </div>
            <span className="text-xl font-black text-white tracking-[0.2em]">
              Trade<span className="text-indigo-500">Finance</span>
            </span>
          </div>

          <h2 className="text-3xl font-black text-white leading-tight tracking-tight mb-10">
            A SECURE TRADE TRANSACTION<br />
            <span className="text-indigo-500">WITH BLOCKCHAIN TECHNOLOGY</span>
          </h2>

          <div className="space-y-6 max-w-xs">
            <Feature text="Automated LC Verification" icon={<ShieldCheck size={16}/>} />
            <Feature text="Distributed Ledger Sync" icon={<Activity size={16}/>} />
            <Feature text="Cross-Border Handshake" icon={<Globe size={16}/>} />
          </div>
        </div>

        {/* ================= RIGHT PANEL ================= */}
        <div className="flex-1 p-10 lg:p-16 bg-black/60 backdrop-blur-2xl border border-white/10 rounded-b-[2.5rem] md:rounded-r-[2.5rem] md:rounded-b-none shadow-[0_40px_120px_rgba(0,0,0,0.7)] relative overflow-hidden">
          <div className="absolute inset-0 pointer-events-none border-glow-soft" />

          <h3 className="text-3xl font-black text-white mb-2">Access To Login</h3>
          <p className="text-slate-500 text-xs font-bold uppercase tracking-[0.25em] mb-10">
            Registered Email and Password required
          </p>

          {error && (
            <div className="flex items-center gap-3 bg-rose-500/10 border border-rose-500/30 text-rose-400 p-4 rounded-2xl text-[10px] mb-8 font-black uppercase tracking-widest animate-shake">
              <ShieldAlert size={16} />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            <Input label="Email ID" icon={<Mail size={18}/>} type="email" onChange={setEmail} />
            <Input label="Password" icon={<Lock size={18}/>} type="password" onChange={setPassword} />

            <button 
              disabled={isSubmitting}
              className="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-black py-5 rounded-2xl transition-all active:scale-[0.98] flex items-center justify-center gap-3 shadow-[0_0_40px_rgba(99,102,241,0.4)] uppercase tracking-[0.25em] text-[10px] border border-indigo-400/30"
            >
              {isSubmitting ? "Loading..." : "Access to Login"}
              {!isSubmitting && <ChevronRight size={16} />}
            </button>
          </form>

          <div className="mt-10 text-center border-t border-white/5 pt-8">
            <p className="text-slate-500 text-xs">
              If you don't have account?
              <Link to="/register" className="text-indigo-400 ml-2 font-bold underline underline-offset-4">
                Register
              </Link>
            </p>
            <p className="mt-8 text-slate-700 text-[10px] font-bold uppercase tracking-[0.3em]">
              All Rights Reserved © 2026 Tharun
            </p>
          </div>
        </div>
      </main>

      {/* ================= GRAPHICS STYLES ================= */}
      <style>{`
        .glass-input {
          width: 100%;
          background: rgba(255,255,255,0.04);
          border: 1px solid rgba(255,255,255,0.12);
          border-radius: 1.25rem;
          padding: 1.15rem 1.15rem 1.15rem 3.5rem;
          color: white;
        }

        .bg-grid {
          background-image:
            linear-gradient(to right, #1e293b 1px, transparent 1px),
            linear-gradient(to bottom, #1e293b 1px, transparent 1px);
          background-size: 30px 30px;
        }

        .bg-noise {
          background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.8' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='.05'/%3E%3C/svg%3E");
        }

        .border-glow {
          box-shadow: inset 0 0 80px rgba(99,102,241,0.15);
        }

        .border-glow-soft {
          box-shadow: inset 0 0 60px rgba(56,189,248,0.15);
        }

        @keyframes float {
          0%,100% { transform: translateY(0); }
          50% { transform: translateY(-20px); }
        }

        .animate-float-slow { animation: float 18s ease-in-out infinite; }
        .animate-float-reverse { animation: float 22s ease-in-out infinite reverse; }

        @keyframes bg-drift {
          from { transform: scale(1.1) translateY(0); }
          to { transform: scale(1.2) translateY(-40px); }
        }

        .animate-bg-drift {
          animation: bg-drift 40s linear infinite alternate;
        }

        @keyframes shake {
          0%,100% { transform: translateX(0); }
          25% { transform: translateX(-4px); }
          75% { transform: translateX(4px); }
        }

        .animate-shake {
          animation: shake 0.4s ease-in-out;
        }
      `}</style>
    </div>
  );
}

function Input({ label, icon, type, onChange }) {
  return (
    <div className="space-y-2 group">
      <label className="text-[10px] font-black text-slate-500 uppercase tracking-[0.25em] ml-2">
        {label}
      </label>
      <div className="relative">
        <span className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500">
          {icon}
        </span>
        <input
          type={type}
          className="glass-input"
          onChange={(e) => onChange(e.target.value)}
          required
        />
      </div>
    </div>
  );
}

function Feature({ text, icon }) {
  return (
    <div className="flex items-center gap-3 text-white/60 text-[11px] font-bold uppercase tracking-widest border border-white/10 bg-white/5 rounded-full px-4 py-2 backdrop-blur-md shadow-inner">
      {icon} {text}
    </div>
  );
}
