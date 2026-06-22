import React, { createContext, useContext, useState, useEffect } from "react";
import axios from "axios";

// 1. Create the Context
const AuthContext = createContext();

// 2. Set up your API base URL (matching port 8000 for FastAPI)
const api = axios.create({
  baseURL: "https://trade-finance.onrender.com",
});

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem("token");
      if (token) {
        // Attach token to headers for the /auth/me call
        api.defaults.headers.common["Authorization"] = `Bearer ${token}`;
        try {
          const res = await api.get("/auth/me"); //
          setUser(res.data);
        } catch (err) {
          localStorage.removeItem("token");
          delete api.defaults.headers.common["Authorization"];
        }
      }
      setLoading(false);
    };
    initAuth();
  }, []);

  const login = async (email, password) => {
    // Matches your LoginIn schema in auth_routes.py
    const res = await api.post("/auth/login", { 
      email: email.toLowerCase().trim(), 
      password 
    });
    
    const { access_token } = res.data;
    localStorage.setItem("token", access_token);
    api.defaults.headers.common["Authorization"] = `Bearer ${access_token}`;
    
    // Fetch user details immediately
    const userRes = await api.get("/auth/me");
    setUser(userRes.data);
  };

  const logout = () => {
    localStorage.removeItem("token");
    delete api.defaults.headers.common["Authorization"];
    setUser(null);
  };

  // Prevent white screen by showing a loading state
  if (loading) {
    return <div className="bg-gray-900 min-h-screen text-white flex items-center justify-center">Loading session...</div>;
  }

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

// 3. Custom hook for easy access
export const useAuth = () => useContext(AuthContext);