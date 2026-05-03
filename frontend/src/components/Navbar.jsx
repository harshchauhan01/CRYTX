import { Link, useLocation } from "react-router-dom";
import "./Navbar.css";

export default function Navbar({ user, balance, onLogout }) {
  const location = useLocation();

  const isActive = (path) => location.pathname === path;

  return (
    <nav className="navbar">
      <div className="navbar-container">
        <Link to="/market" className="navbar-logo">
          <span className="logo-mark" aria-hidden="true" />
          <span className="logo-text">CRYTX</span>
        </Link>
        
        <div className="navbar-links">
          <Link 
            to="/market" 
            className={`nav-link ${isActive("/market") ? "active" : ""}`}
          >
            Market
          </Link>
          <Link 
            to="/portfolio" 
            className={`nav-link ${isActive("/portfolio") ? "active" : ""}`}
          >
            Portfolio
          </Link>
          <Link 
            to="/leaderboard" 
            className={`nav-link ${isActive("/leaderboard") ? "active" : ""}`}
          >
            Leaderboard
          </Link>
        </div>

        <div className="navbar-user">
          <div className="user-details">
            {user && <span className="user-email">{user}</span>}
            {balance !== undefined && balance !== null && (
              <span className="user-balance">
                <span className="balance-label">Balance:</span>
                <span className="balance-value">CR {parseFloat(balance).toFixed(2)}</span>
              </span>
            )}
          </div>
          <button className="logout-btn" onClick={onLogout}>
            Logout
          </button>
        </div>
      </div>
    </nav>
  );
}
