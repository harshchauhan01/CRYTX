import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import "./Navbar.css";

export default function Navbar({ user, balance, onLogout }) {
  const location = useLocation();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const isActive = (path) => location.pathname === path;

  return (
    <nav className="navbar">
      <div className="navbar-container">
        {/* Logo — links back to home */}
        <Link to="/" className="navbar-logo">
          <span className="crystal-logo" />
          <span className="logo-text">CRYTX</span>
        </Link>

        <div className={`navbar-links ${isMenuOpen ? "open" : ""}`}>
          <Link to="/"           className={`nav-link ${isActive("/")           ? "active" : ""}`} onClick={() => setIsMenuOpen(false)}>HOME</Link>
          <Link to="/market"     className={`nav-link ${isActive("/market")     ? "active" : ""}`} onClick={() => setIsMenuOpen(false)}>MARKET</Link>
          <Link to="/portfolio"  className={`nav-link ${isActive("/portfolio")  ? "active" : ""}`} onClick={() => setIsMenuOpen(false)}>PORTFOLIO</Link>
          <Link to="/leaderboard"className={`nav-link ${isActive("/leaderboard")? "active" : ""}`} onClick={() => setIsMenuOpen(false)}>LEADERS</Link>
        </div>

        <div className="navbar-user">
          <div className="user-details">
            {user && <span className="user-email">{user}</span>}
            {balance != null && (
              <span className="user-balance">
                <span className="balance-label">◆</span>
                <span className="balance-value">
                  {parseFloat(balance).toLocaleString("en-US", { minimumFractionDigits: 2 })}
                </span>
              </span>
            )}
          </div>
          <button className="logout-btn" onClick={onLogout}>[ EXIT ]</button>
        </div>

        <button className="mobile-menu-btn" onClick={() => setIsMenuOpen(!isMenuOpen)}>
          {isMenuOpen ? "[ X ]" : "[ MENU ]"}
        </button>
      </div>
    </nav>
  );
}
