import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import axios from "axios";
import Button from "../components/Button";
import "./AuthPage.css";

const API_BASE = "http://127.0.0.1:8001/api/auth";

export default function Signup({ onSignup }) {
  const [form, setForm] = useState({ email: "", username: "", password: "" });
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
    if (!form.email || !form.username || !form.password) {
      setError("All fields are required");
      return;
    }
    
    if (form.password.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }

    setLoading(true);
    setError("");
    
    try {
      const response = await axios.post(`${API_BASE}/signup/`, form);
      
      if (!response.data.access) {
        throw new Error("No access token received");
      }
      
      localStorage.setItem("access_token", response.data.access);
      if (response.data.refresh) {
        localStorage.setItem("refresh_token", response.data.refresh);
      }
      localStorage.setItem("user_email", form.email);
      
      if (onSignup) onSignup();
      navigate("/market");
    } catch (err) {
      const errorMsg = err.response?.data?.email?.[0] ||
                       err.response?.data?.username?.[0] ||
                       err.response?.data?.password?.[0] ||
                       err.response?.data?.error ||
                       err.response?.data?.detail ||
                       err.message ||
                       "Signup failed. Try different credentials.";
      setError(errorMsg);
      console.error("Signup error:", err);
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

        <h2>Join the Crystal Economy</h2>
        <p className="auth-subtitle">Start your trading journey and build an empire.</p>

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
            <label htmlFor="username">Username</label>
            <input
              id="username"
              type="text"
              name="username"
              placeholder="TraderName"
              value={form.username}
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
            {loading ? "Creating account..." : "Sign Up"}
          </Button>
        </form>

        <div className="auth-footer">
          <p>
            Already have an account?{" "}
            <Link to="/login" className="auth-link">
              Login here
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