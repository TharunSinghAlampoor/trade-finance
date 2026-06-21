import { Navigate } from "react-router-dom";
import { useEffect, useState } from "react";
import api from "../api/axios";

export default function Protected({ children }) {
  const token = localStorage.getItem("access_token");
  const [allowed, setAllowed] = useState(token ? null : false);

  useEffect(() => {
    if (!token) return;

    let active = true;

    api.get("/auth/me")
      .then(() => active && setAllowed(true))
      .catch(() => active && setAllowed(false));

    return () => {
      active = false;
    };
  }, [token]);

  if (allowed === null) return <div>Checking auth...</div>;
  if (!allowed) return <Navigate to="/" />;

  return children;
}
