import { useEffect, useState } from "react";
import api from "../api/axios";

export default function Users() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);

  const [showForm, setShowForm] = useState(false);
  const [editingUser, setEditingUser] = useState(null);

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("corp");
  const [orgId, setOrgId] = useState("");
  const [orgName, setOrgName] = useState("");

  const [msg, setMsg] = useState("");

  useEffect(() => {
    loadUsers();
  }, []);

  async function loadUsers() {
    setLoading(true);
    const res = await api.get("/user/");
    setUsers(res.data);
    setLoading(false);
  }

  function openCreate() {
    setEditingUser(null);
    setName("");
    setEmail("");
    setPassword("");
    setRole("corp");
    setOrgId("");
    setOrgName("");
    setMsg("");
    setShowForm(true);
  }

  function openEdit(user) {
    setEditingUser(user);
    setName(user.name);
    setEmail(user.email);
    setRole(user.role);
    setPassword("");
    setOrgId(user.org_id ?? "");
    setOrgName(user.org_name ?? "");
    setMsg("");
    setShowForm(true);
  }

  async function submitUser(e) {
    e.preventDefault();
    setMsg("");

    if (!name || !email || !role) {
      setMsg("Name, Email and Role are required");
      return;
    }

    if (!editingUser) {
      if (!password || !orgId || !orgName) {
        setMsg("Password, Org ID and Org Name are required");
        return;
      }

      await api.post("/user/", {
        name,
        email,
        password,
        role,
        org_id: Number(orgId),
        org_name: orgName,
      });
    } else {
      await api.put(`/user/${editingUser.id}`, {
        name,
        email,
        role,
      });
    }

    setShowForm(false);
    loadUsers();
  }

  async function deleteUser(id) {
    if (!window.confirm("Delete this user?")) return;
    await api.delete(`/user/${id}`);
    loadUsers();
  }

  return (
    <div className="users-root">
      <style>{`
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

/* ================= ROOT ================= */
.users-root {
  font-family: 'Inter', system-ui, sans-serif;
  min-height: 100vh;
  padding: 32px;
  color: #083344;
  background: linear-gradient(
    180deg,
    #85DECB 0%,
    #9fe6d7 35%,
    #c6f3ea 70%,
    #e9fbf7 100%
  );
}

/* ================= CARD ================= */
.card {
  background: #f0fdfa;
  border: 1px solid #5ecfbd;
  border-radius: 18px;
  padding: 16px;
  box-shadow:
    0 4px 10px rgba(8, 51, 68, 0.08),
    0 20px 40px rgba(8, 51, 68, 0.12);
}

/* ================= ROLE BADGE ================= */
.badge {
  font-size: 11px;
  text-transform: uppercase;
  padding: 4px 12px;
  border-radius: 999px;
  background: linear-gradient(135deg, #85DECB, #c6f3ea);
  border: 1px solid #5ecfbd;
  color: #083344;
  font-weight: 700;
}

/* ================= BUTTONS ================= */
.btn {
  font-weight: 600;
  padding: 6px 14px;
  border-radius: 10px;
  font-size: 13px;
  color: #083344;
}

.btn-primary {
  background: linear-gradient(135deg, #14b8a6, #0d9488);
  color: #ecfeff;
  box-shadow: 0 8px 20px rgba(13, 148, 136, 0.45);
}

.btn-danger {
  color: #b91c1c;
}

.btn:hover {
  opacity: 0.95;
}

/* ================= INPUTS ================= */
.input {
  width: 100%;
  background: linear-gradient(180deg, #ffffff, #ecfeff);
  border: 1px solid #5ecfbd;
  border-radius: 10px;
  padding: 10px 12px;
  color: #083344;
  outline: none;
  font-family: 'Inter', system-ui;
}

.input::placeholder {
  color: #0f766e;
}

.input:focus {
  border-color: #14b8a6;
  box-shadow: 0 0 0 2px rgba(20, 184, 166, 0.35);
}

/* ================= MODAL OVERLAY ================= */
.fixed.inset-0 {
  background: rgba(133, 222, 203, 0.85);
  backdrop-filter: blur(6px);
}

/* ================= TEXT HELPERS ================= */
.text-gray-400 {
  color: #0f766e;
}

.text-cyan-400 {
  color: #0d9488;
}

.font-mono {
  font-family: 'JetBrains Mono', monospace;
}
      `}</style>

      {/* HEADER */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold">System Users</h1>
        <button onClick={openCreate} className="btn btn-primary">
          + Add User
        </button>
      </div>

      {/* CARDS */}
      {loading ? (
        <p className="text-gray-400">Loading users…</p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {users.map((u) => (
            <div key={u.id} className="card space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-lg">{u.name}</h3>
                <span className="badge">{u.role}</span>
              </div>

              <div className="text-xs font-mono text-gray-400">
                ID: {u.id}
              </div>

              <div className="text-sm">{u.email}</div>

              <div className="text-xs text-gray-400">
                Org: {u.org_name} (#{u.org_id})
              </div>

              <div className="flex gap-3 pt-2">
                <button
                  onClick={() => openEdit(u)}
                  className="btn text-cyan-400"
                >
                  Edit
                </button>
                <button
                  onClick={() => deleteUser(u.id)}
                  className="btn btn-danger"
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* MODAL */}
      {showForm && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
          <form
            onSubmit={submitUser}
            className="card w-full max-w-md space-y-3"
          >
            <h2 className="text-lg font-semibold">
              {editingUser ? "Edit User" : "Create User"}
            </h2>

            <input
              className="input"
              placeholder="Name"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />

            <input
              className="input"
              placeholder="Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />

            {!editingUser && (
              <>
                <input
                  className="input"
                  type="password"
                  placeholder="Password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />

                <input
                  className="input"
                  placeholder="Org ID"
                  type="number"
                  value={orgId}
                  onChange={(e) => setOrgId(e.target.value)}
                />

                <input
                  className="input"
                  placeholder="Org Name"
                  value={orgName}
                  onChange={(e) => setOrgName(e.target.value)}
                />
              </>
            )}

            <select
              className="input"
              value={role}
              onChange={(e) => setRole(e.target.value)}
            >
              <option value="admin">Admin</option>
              <option value="auditor">Auditor</option>
              <option value="bank">Bank</option>
              <option value="corp">Corp</option>
            </select>

            {msg && <p className="text-emerald-600 text-sm">{msg}</p>}

            <div className="flex justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className="btn"
              >
                Cancel
              </button>
              <button type="submit" className="btn btn-primary">
                Save
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
