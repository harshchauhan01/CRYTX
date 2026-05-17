import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { useState, useEffect, useCallback } from "react";
import Navbar from "./components/Navbar";
import ToastContainer from "./components/Toast";
import HomePage from "./pages/HomePage";
import LoginPage from "./pages/LoginPage";
import SignupPage from "./pages/SignupPage";
import MarketDashboard from "./pages/MarketDashboard";
import Portfolio from "./pages/Portfolio";
import Leaderboard from "./pages/Leaderboard";
import { soundFX } from "./utils/soundFX";
import api from "./utils/api";
import "./globals.css";

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(!!localStorage.getItem("crytx_access_token"));
  const [user, setUser] = useState(null);
  const [balance, setBalance] = useState(0);

  const fetchProfile = useCallback(async () => {
    try {
      const res = await api.get("/auth/profile/");
      setUser(res.data);
      setBalance(res.data.wallet?.balance || 0);
    } catch {
      handleLogout();
    }
  }, []);

  useEffect(() => {
    if (isAuthenticated) {
      fetchProfile();
      soundFX.init();
    }
  }, [isAuthenticated, fetchProfile]);

  const handleLogin = () => {
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    localStorage.removeItem("crytx_access_token");
    localStorage.removeItem("crytx_refresh_token");
    setIsAuthenticated(false);
    setUser(null);
    setBalance(0);
  };

  return (
    <BrowserRouter>
      <div className="app-shell">
        {isAuthenticated && (
          <Navbar user={user} balance={balance} onLogout={handleLogout} />
        )}
        <div className={isAuthenticated ? "app-content" : ""}>
          <Routes>
            <Route path="/" element={<HomePage isAuthenticated={isAuthenticated} />} />
            <Route
              path="/login"
              element={isAuthenticated ? <Navigate to="/market" /> : <LoginPage onLogin={handleLogin} />}
            />
            <Route
              path="/signup"
              element={isAuthenticated ? <Navigate to="/market" /> : <SignupPage onLogin={handleLogin} />}
            />
            <Route
              path="/market"
              element={isAuthenticated ? <MarketDashboard onTradeComplete={fetchProfile} /> : <Navigate to="/login" />}
            />
            <Route
              path="/portfolio"
              element={isAuthenticated ? <Portfolio /> : <Navigate to="/login" />}
            />
            <Route
              path="/leaderboard"
              element={isAuthenticated ? <Leaderboard /> : <Navigate to="/login" />}
            />
            {/* Catch-all fallback */}
            <Route path="*" element={<Navigate to={isAuthenticated ? "/market" : "/"} />} />
          </Routes>
        </div>
        <ToastContainer />
      </div>
    </BrowserRouter>
  );
}

export default App;
