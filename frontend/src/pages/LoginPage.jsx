import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import axios from "axios";
import Button from "../components/Button";
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
    
    // Validation
    if (!form.email || !form.password) {
      setError("Email and password are required");
      return;
    }

    setLoading(true);
    setError("");
    
    try {
      const response = await axios.post(`${API_BASE}/login/`, form);
      
      if (!response.data.access) {
        throw new Error("No access token received");
      }
      
      localStorage.setItem("access_token", response.data.access);
      if (response.data.refresh) {
        localStorage.setItem("refresh_token", response.data.refresh);
      }
      localStorage.setItem("user_email", form.email);
      
      if (onLogin) onLogin();
      navigate("/market");
    } catch (err) {
      const errorMsg = err.response?.data?.error || 
                       err.response?.data?.detail ||
                       err.message ||
                       "Login failed. Please try again.";
      setError(errorMsg);
      console.error("Login error:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-container">
        <div className="auth-logo">
          <span className="logo-mark" aria-hidden="true" />
          <h1>CRYTX</h1>
        </div>

        <h2>Welcome Back, Trader</h2>
        <p className="auth-subtitle">Trade crystals. Build wealth. Dominate markets.</p>

        <form onSubmit={handleSubmit} className="auth-form">
          {error && <div className="error-message">{error}</div>}

          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              name="email"
              placeholder="your@email.com"
              value={form.email}
              onChange={handleChange}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              name="password"
              placeholder="••••••••"
              value={form.password}
              onChange={handleChange}
              required
            />
          </div>

          <Button
            variant="primary"
            size="lg"
            fullWidth
            type="submit"
            disabled={loading}
          >
            {loading ? "Logging in..." : "Login"}
          </Button>
        </form>

        <div className="auth-footer">
          <p>
            Don't have an account?{" "}
            <Link to="/signup" className="auth-link">
              Sign up here
            </Link>
          </p>
        </div>
      </div>

      <div className="auth-decoration">
        <div className="pixel-crystal pixel-crystal-1" />
        <div className="pixel-crystal pixel-crystal-2" />
        <div className="pixel-crystal pixel-crystal-3" />
      </div>
    </div>
  );
}