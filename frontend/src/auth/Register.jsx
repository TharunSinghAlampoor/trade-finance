import { useState } from "react";
import api from "../api/axios";
import { useNavigate, Link } from "react-router-dom";
import { 
  UserPlus, ShieldCheck, Mail, Lock, 
  Landmark, Globe, ChevronRight, ShieldAlert 
} from "lucide-react";

/**
 * Institutional Registration Portal v3.1
 * Developed by: Tharun
 * All Rights Reserved © 2026 Tharun
 */
export default function Register() {
  const [formData, setFormData] = useState({
    name: "", email: "", password: "", role: "corporate", org_name: ""
  });
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const navigate = useNavigate();

  const handleRegister = async (e) => {
    e.preventDefault();
    setError("");
    setIsSubmitting(true);
    
    try {
      // Logic targets @router.post("/auth/register")
      await api.post("/auth/register", formData);
      navigate("/login");
    } catch (err) {
      setError(err.response?.data?.detail || "Node registration sequence failed.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen relative flex items-center justify-center font-sans overflow-hidden bg-black">
      
      {/* CINEMATIC BACKGROUND (Matches Login) */}
      <div 
        className="absolute inset-0 z-0 bg-cover bg-center bg-no-repeat opacity-40"
        style={{ 
          backgroundImage: `url('https://images.unsplash.com/photo-1518458028785-8fbcd101ebb9?auto=format&fit=crop&q=80&w=2070')`,
          filter: 'brightness(0.3) grayscale(0.2)'
        }}
      />

      {/* GRAPHIC OVERLAYS */}
      <div className="absolute inset-0 z-10 bg-gradient-to-tr from-black via-black/80 to-indigo-900/20" />
      <div className="absolute inset-0 z-10 opacity-10 [background-image:linear-gradient(to_right,#1e293b_1px,transparent_1px),linear-gradient(to_bottom,#1e293b_1px,transparent_1px)] [background-size:40px_40px]" />

      {/* REGISTRATION MODULE */}
      <main className="relative z-20 w-full max-w-5xl flex flex-col md:flex-row p-4 animate-in fade-in slide-in-from-bottom-4 duration-1000">
        
        {/* LEFT PANEL: PROTOCOL INFO */}
        <div className="hidden md:flex flex-1 p-10 lg:p-14 bg-white/5 backdrop-blur-xl border border-white/10 rounded-l-[2.5rem] flex-col justify-between">
          <div>
            <div className="flex items-center gap-4 mb-14">
              <div className="p-3 bg-indigo-600 rounded-2xl shadow-lg shadow-indigo-600/40">
                <Globe className="text-white" size={24} />
              </div>
              <span className="text-xl font-black text-white tracking-[0.2em] ">
                Trade<span className="text-indigo-500 font-sans not-italic">Finance</span>
              </span>
            </div>

            <h2 className="text-4xl font-black text-white leading-tight tracking-tighter mb-8">
              TRADE <br />
              <span className="text-indigo-500 font-serif">TRANSACTIONS</span>
            </h2>
            
            <div className="space-y-6">
              <RequirementItem icon={<ShieldCheck size={18}/>} text="Distributed Identity Verification" />
              <RequirementItem icon={<Landmark size={18}/>} text="Regulatory Compliance Binding" />
              <RequirementItem icon={<Lock size={18}/>} text="SHA-256 Key Pair Generation" />
            </div>
          </div>

          <div className="text-[10px] font-bold text-slate-500 uppercase tracking-[0.4em]">
             <span className="text-slate-400"></span>
          </div>
        </div>

        {/* RIGHT PANEL: REGISTRATION FORM */}
        <div className="flex-[1.2] p-10 lg:p-14 bg-black/60 backdrop-blur-2xl border border-white/10 rounded-2xl md:rounded-l-none md:rounded-r-[2.5rem] shadow-2xl">
          <div className="mb-10 text-center md:text-left">
            <h3 className="text-3xl font-black text-white mb-2 tracking-tight uppercase">CREATE A NEW ACCOUNT</h3>
            <p className="text-slate-500 text-[10px] font-bold uppercase tracking-[0.2em]">REGISTER WITH CORPORATE ROLE</p>
          </div>

          {error && (
            <div className="flex items-center gap-3 bg-rose-500/10 border border-rose-500/20 text-rose-400 p-4 rounded-xl text-[10px] mb-8 font-black uppercase tracking-widest animate-pulse">
              <ShieldAlert size={16} />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleRegister} className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="md:col-span-2 space-y-1">
              <label className="text-[10px] font-black text-slate-500 uppercase tracking-[0.2em] ml-2">Full Name</label>
              <input 
                type="text" 
                className="glass-input-sm" 
                placeholder="FULL NAME"
                onChange={(e) => setFormData({...formData, name: e.target.value})} 
                required 
              />
            </div>

            <div className="space-y-1">
              <label className="text-[10px] font-black text-slate-500 uppercase tracking-[0.2em] ml-2">Email</label>
              <input 
                type="email" 
                className="glass-input-sm" 
                placeholder="name@example.com"
                onChange={(e) => setFormData({...formData, email: e.target.value})} 
                required 
              />
            </div>

            <div className="space-y-1">
              <label className="text-[10px] font-black text-slate-500 uppercase tracking-[0.2em] ml-2">Password</label>
              <input 
                type="password" 
                className="glass-input-sm" 
                placeholder="xxxxxxx"
                onChange={(e) => setFormData({...formData, password: e.target.value})} 
                required 
              />
            </div>

            <div className="space-y-1">
              <label className="text-[10px] font-black text-slate-500 uppercase tracking-[0.2em] ml-2">Role</label>
              <select 
                className="glass-input-sm appearance-none bg-[#0b1224]" 
                onChange={(e) => setFormData({...formData, role: e.target.value})}
              >
                <option value="corporate">CORPORATE</option>
                <option value="bank">BANK</option>
              </select>
            </div>

            <div className="space-y-1">
              <label className="text-[10px] font-black text-slate-500 uppercase tracking-[0.2em] ml-2">Organization</label>
              <input 
                type="text" 
                className="glass-input-sm" 
                placeholder="ORG NAME"
                onChange={(e) => setFormData({...formData, org_name: e.target.value})} 
                required 
              />
            </div>

            <button 
              disabled={isSubmitting}
              className="md:col-span-2 bg-indigo-600 hover:bg-indigo-500 text-white font-black py-5 rounded-2xl transition-all active:scale-[0.98] flex items-center justify-center gap-3 shadow-xl shadow-indigo-600/20 uppercase tracking-[0.2em] text-[10px] mt-2 border border-indigo-400/20"
            >
              {isSubmitting ? "Creating Profile..." : "Register"}
              {!isSubmitting && <ChevronRight size={16} />}
            </button>
          </form>

          <div className="mt-10 text-center border-t border-white/5 pt-8">
            <p className="text-slate-500 text-[10px] font-bold uppercase tracking-widest">
              Already Have a Account?{' '}
              <Link to="/login" className="text-indigo-400 hover:text-indigo-300 ml-1 transition-all underline decoration-indigo-500/30 underline-offset-4">
                Return to Login
              </Link>
            </p>
            <p className="mt-8 text-slate-700 text-[10px] font-bold uppercase tracking-[0.3em]">
              All Rights Reserved © 2026 Tharun
            </p>
          </div>
        </div>
      </main>

      <style>{`
        .glass-input-sm {
          width: 100%;
          background: rgba(255, 255, 255, 0.03);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 1rem;
          padding: 1rem;
          color: white;
          font-size: 13px;
          outline: none;
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .glass-input-sm:focus {
          background: rgba(255, 255, 255, 0.08);
          border-color: #6366f1;
          box-shadow: 0 0 20px rgba(99, 102, 241, 0.1);
        }
      `}</style>
    </div>
  );
}

function RequirementItem({ icon, text }) {
  return (
    <div className="flex items-center gap-4 text-white/50 text-[11px] font-bold uppercase tracking-widest">
      <div className="text-indigo-500">{icon}</div>
      {text}
    </div>
  );
}