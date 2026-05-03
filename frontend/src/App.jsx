import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { useState, useEffect } from "react";
import Signup from "./pages/SignupPage";
import Login from "./pages/LoginPage";
import MarketDashboard from "./pages/MarketDashboard";
import Portfolio from "./pages/Portfolio";
import Leaderboard from "./pages/Leaderboard";
import Navbar from "./components/Navbar";
import "./globals.css";
import "./App.css";

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [balance, setBalance] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (token) {
      setIsAuthenticated(true);
      const userEmail = localStorage.getItem("user_email");
      setUser(userEmail);
      const savedBalance = localStorage.getItem("user_balance");
      if (savedBalance) setBalance(parseFloat(savedBalance));
    }
    setLoading(false);
  }, []);

  const handleLogin = () => {
    const userEmail = localStorage.getItem("user_email");
    setUser(userEmail);
    setIsAuthenticated(true);
  };

  const handleSignup = () => {
    const userEmail = localStorage.getItem("user_email");
    setUser(userEmail);
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

  if (loading) {
    return <div>Loading...</div>;
  }

  return (
    <BrowserRouter>
      <div className="app-shell">
        {isAuthenticated && <Navbar user={user} balance={balance} onLogout={handleLogout} />}
        <Routes>
          <Route 
            path="/signup" 
            element={isAuthenticated ? <Navigate to="/market" /> : <Signup onSignup={handleSignup} />} 
          />
          <Route 
            path="/login" 
            element={isAuthenticated ? <Navigate to="/market" /> : <Login onLogin={handleLogin} />} 
          />
          <Route 
            path="/market" 
            element={isAuthenticated ? <MarketDashboard onBalanceUpdate={updateBalance} /> : <Navigate to="/login" />} 
          />
          <Route 
            path="/portfolio" 
            element={isAuthenticated ? <Portfolio onBalanceUpdate={updateBalance} /> : <Navigate to="/login" />} 
          />
          <Route 
            path="/leaderboard" 
            element={isAuthenticated ? <Leaderboard /> : <Navigate to="/login" />} 
          />
          <Route 
            path="/" 
            element={isAuthenticated ? <Navigate to="/market" /> : <Navigate to="/login" />} 
          />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;