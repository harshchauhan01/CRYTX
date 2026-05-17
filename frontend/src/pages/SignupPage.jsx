import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { soundFX } from "../utils/soundFX";
import api from "../utils/api";
import "./AuthPage.css";

export default function SignupPage({ onLogin }) {
  const [form, setForm] = useState({ email: "", username: "", password: "", password_confirm: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    soundFX.click();
    setError("");

    if (form.password !== form.password_confirm) {
      soundFX.error();
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);
    try {
      const res = await api.post("/auth/signup/", form);
      localStorage.setItem("crytx_access_token", res.data.tokens.access);
      localStorage.setItem("crytx_refresh_token", res.data.tokens.refresh);
      onLogin();
      navigate("/market");
    } catch (err) {
      soundFX.error();
      const errors = err.response?.data;
      if (errors) {
        const msg = Object.values(errors).flat().join(" ");
        setError(msg);
      } else {
        setError("Registration failed.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card panel-border">
        <div className="auth-diamond">◆</div>
        <h2 className="auth-title">NEW CITIZEN</h2>
        <p className="auth-subtitle">REGISTER FOR THE SYNDICATE</p>

        {error && <div className="auth-error">{error}</div>}

        <form onSubmit={handleSubmit} className="auth-form">
          <input className="input" placeholder="EMAIL" type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required />
          <input className="input" placeholder="USERNAME" value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} required />
          <input className="input" type="password" placeholder="PASSWORD" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required />
          <input className="input" type="password" placeholder="CONFIRM PASSWORD" value={form.password_confirm} onChange={(e) => setForm({ ...form, password_confirm: e.target.value })} required />
          <button className="btn btn-primary auth-submit" disabled={loading} type="submit">
            {loading ? "REGISTERING..." : "CREATE ACCOUNT"}
          </button>
        </form>

        <p className="auth-switch">
          Already registered? <Link to="/login">Login here</Link>
        </p>
      </div>
    </div>
  );
}
