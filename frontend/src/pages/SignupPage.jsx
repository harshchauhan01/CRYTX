import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import axios from "axios";
import "./AuthPage.css";

const API_BASE = "http://127.0.0.1:8001/api/auth";

export default function Signup({ onSignup }) {
  const [form, setForm] = useState({ email: "", username: "", password: "", password_confirm: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm(prev => ({ ...prev, [name]: value }));
    if (error) setError("");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.email || !form.username || !form.password || !form.password_confirm) { setError("All fields required"); return; }
    if (form.password.length < 8) { setError("Access code must be 8+ chars"); return; }
    if (form.password !== form.password_confirm) { setError("Passwords do not match"); return; }
    setLoading(true); setError("");
    try {
      const res = await axios.post(`${API_BASE}/signup/`, form);
      if (!res.data.access) throw new Error("No token");
      localStorage.setItem("access_token", res.data.access);
      localStorage.setItem("refresh_token", res.data.refresh || "");
      localStorage.setItem("user_email", form.email);
      if (onSignup) onSignup();
      navigate("/market");
    } catch (err) {
      const d = err.response?.data;
      const msg = d?.email?.[0] || d?.username?.[0] || d?.password?.[0] || d?.error || d?.detail || "Registration failed.";
      setError(msg);
    } finally { setLoading(false); }
  };

  return (
    <div className="auth-page">
      <div className="auth-wrap">
        <span className="auth-crystal">◆</span>
        <div className="auth-headline">
          <span className="line1">CLAIM YOUR</span>
          <span className="line2">HANDLE.</span>
        </div>
        <p className="auth-sub">
          Register your trader identity and step onto the exchange floor.
        </p>

        <div className="auth-card">
          <form onSubmit={handleSubmit} className="auth-form">
            {error && <div className="auth-error">▶ {error}</div>}

            <div className="auth-form-group">
              <label className="auth-form-label" htmlFor="email">HANDLE_EMAIL</label>
              <input
                id="email" type="email" name="email"
                className="auth-form-input"
                placeholder="trader@wasteland.net"
                value={form.email} onChange={handleChange} required
                autoComplete="email"
              />
            </div>

            <div className="auth-form-group">
              <label className="auth-form-label" htmlFor="username">TRADER_NAME</label>
              <input
                id="username" type="text" name="username"
                className="auth-form-input"
                placeholder="VAULT_DWELLER"
                value={form.username} onChange={handleChange} required
                autoComplete="username"
              />
            </div>

            <div className="auth-form-group">
              <label className="auth-form-label" htmlFor="password">ACCESS_CODE</label>
              <input
                id="password" type="password" name="password"
                className="auth-form-input"
                placeholder="min 8 characters"
                value={form.password} onChange={handleChange} required
                autoComplete="new-password"
              />
            </div>

            <div className="auth-form-group">
              <label className="auth-form-label" htmlFor="password_confirm">CONFIRM_CODE</label>
              <input
                id="password_confirm" type="password" name="password_confirm"
                className="auth-form-input"
                placeholder="repeat access code"
                value={form.password_confirm} onChange={handleChange} required
                autoComplete="new-password"
              />
            </div>

            <button type="submit" className="auth-submit-btn" disabled={loading}>
              {loading ? "INITIALIZING..." : "► ENTER MARKET"}
            </button>
          </form>
        </div>

        <p className="auth-starter-note">◆ FREE STARTER WALLET · <span>10,000</span> · CRYSTALS ON ENTRY</p>
        <div className="auth-footer" style={{ marginTop: 12 }}>
          ALREADY REGISTERED?&nbsp;
          <Link to="/login" className="auth-footer-link">JACK IN ►</Link>
        </div>
      </div>
    </div>
  );
}