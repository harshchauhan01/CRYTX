import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import axios from "axios";
import "./AuthPage.css";

const API_BASE = "http://127.0.0.1:8001/api/auth";

export default function Login({ onLogin }) {
  const [form, setForm] = useState({ email: "", password: "" });
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
    if (!form.email || !form.password) { setError("All fields required"); return; }
    setLoading(true); setError("");
    try {
      const res = await axios.post(`${API_BASE}/login/`, form);
      if (!res.data.access) throw new Error("No token");
      localStorage.setItem("access_token", res.data.access);
      localStorage.setItem("refresh_token", res.data.refresh || "");
      localStorage.setItem("user_email", form.email);
      if (onLogin) onLogin();
      navigate("/market");
    } catch (err) {
      setError(err.response?.data?.error || err.response?.data?.detail || "Access denied. Check credentials.");
    } finally { setLoading(false); }
  };

  return (
    <div className="auth-page">
      <div className="auth-wrap">
        <span className="auth-crystal">◆</span>
        <div className="auth-headline">
          <span className="line1">JACK IN.</span>
          <span className="line2">SURVIVE.</span>
        </div>
        <p className="auth-sub">
          The wasteland doesn't wait. Access your terminal<br />and step onto the exchange floor.
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
              <label className="auth-form-label" htmlFor="password">ACCESS_CODE</label>
              <input
                id="password" type="password" name="password"
                className="auth-form-input"
                placeholder="••••••••"
                value={form.password} onChange={handleChange} required
                autoComplete="current-password"
              />
            </div>

            <button type="submit" className="auth-submit-btn" disabled={loading}>
              {loading ? "CONNECTING..." : "► ENTER MARKET"}
            </button>
          </form>
        </div>

        <div className="auth-footer">
          NO ACCOUNT?&nbsp;
          <Link to="/signup" className="auth-footer-link">CLAIM YOUR HANDLE ►</Link>
        </div>
      </div>
    </div>
  );
}