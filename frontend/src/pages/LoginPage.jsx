import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { soundFX } from "../utils/soundFX";
import api from "../utils/api";
import "./AuthPage.css";

export default function LoginPage({ onLogin }) {
  const [form, setForm] = useState({ username: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    soundFX.click();
    setError("");
    setLoading(true);
    try {
      const res = await api.post("/auth/login/", form);
      localStorage.setItem("crytx_access_token", res.data.access);
      localStorage.setItem("crytx_refresh_token", res.data.refresh);
      onLogin();
      navigate("/market");
    } catch (err) {
      soundFX.error();
      setError(err.response?.data?.detail || "Login failed. Check your credentials.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card panel-border">
        <div className="auth-diamond">◆</div>
        <h2 className="auth-title">SYSTEM LOGIN</h2>
        <p className="auth-subtitle">ACCESS THE CRYSTAL EXCHANGE</p>

        {error && <div className="auth-error">{error}</div>}

        <form onSubmit={handleSubmit} className="auth-form">
          <input
            className="input"
            placeholder="USERNAME"
            value={form.username}
            onChange={(e) => setForm({ ...form, username: e.target.value })}
            required
          />
          <input
            className="input"
            type="password"
            placeholder="PASSWORD"
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
            required
          />
          <button className="btn btn-primary auth-submit" disabled={loading} type="submit">
            {loading ? "AUTHENTICATING..." : "LOGIN"}
          </button>
        </form>

        <p className="auth-switch">
          New citizen? <Link to="/signup">Register here</Link>
        </p>
      </div>
    </div>
  );
}
