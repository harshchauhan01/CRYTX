import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { useState, useEffect } from "react";
import Signup from "./pages/SignupPage";
import Login from "./pages/LoginPage";
import HomePage from "./pages/HomePage";
import MarketDashboard from "./pages/MarketDashboard";
import Portfolio from "./pages/Portfolio";
import Leaderboard from "./pages/Leaderboard";
import Navbar from "./components/Navbar";
import "./globals.css";
import "./App.css";

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user,    setUser]    = useState(null);
  const [balance, setBalance] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (token) {
      setIsAuthenticated(true);
      setUser(localStorage.getItem("user_email"));
      const saved = localStorage.getItem("user_balance");
      if (saved) setBalance(parseFloat(saved));
    }
    setLoading(false);
  }, []);

  const handleLogin = () => {
    setUser(localStorage.getItem("user_email"));
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("user_email");
    localStorage.removeItem("user_balance");
    setIsAuthenticated(false);
    setUser(null);
    setBalance(null);
  };

  const updateBalance = (newBalance) => {
    setBalance(newBalance);
    localStorage.setItem("user_balance", newBalance.toString());
  };

  if (loading) return (
    <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: "#050d12" }}>
      <div className="px-loader">INITIALIZING SYSTEM...</div>
    </div>
  );

  return (
    <BrowserRouter>
      <div className="app-shell">
        {/* Navbar only shown on authenticated inner pages */}
        {isAuthenticated && (
          <Navbar user={user} balance={balance} onLogout={handleLogout} />
        )}

        <Routes>
          {/* Public home page */}
          <Route path="/"
            element={<HomePage isAuthenticated={isAuthenticated} />}
          />
          {/* Auth */}
          <Route path="/login"
            element={isAuthenticated ? <Navigate to="/market" /> : <Login onLogin={handleLogin} />}
          />
          <Route path="/signup"
            element={isAuthenticated ? <Navigate to="/market" /> : <Signup onSignup={handleLogin} />}
          />
          {/* Protected trading pages */}
          <Route path="/market"
            element={isAuthenticated ? <MarketDashboard onBalanceUpdate={updateBalance} /> : <Navigate to="/login" />}
          />
          <Route path="/portfolio"
            element={isAuthenticated ? <Portfolio onBalanceUpdate={updateBalance} /> : <Navigate to="/login" />}
          />
          <Route path="/leaderboard"
            element={isAuthenticated ? <Leaderboard /> : <Navigate to="/login" />}
          />
          {/* Fallback route */}
          <Route path="*"
            element={<Navigate to={isAuthenticated ? "/market" : "/"} />}
          />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;