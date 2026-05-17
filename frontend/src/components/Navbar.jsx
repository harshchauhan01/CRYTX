import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { soundFX } from "../utils/soundFX";
import "./Navbar.css";

export default function Navbar({ user, balance, onLogout }) {
  const location = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);

  const links = [
    { to: "/market", label: "TRADE" },
    { to: "/portfolio", label: "PORTFOLIO" },
    { to: "/leaderboard", label: "LEADERBOARD" },
  ];

  return (
    <nav className="navbar">
      <div className="nav-inner">
        <Link to="/" className="nav-logo" onMouseEnter={() => soundFX.hover()}>
          <span className="logo-icon">◆</span>
          <span className="logo-text">CRYTX</span>
        </Link>

        <button
          className="mobile-menu-btn"
          onClick={() => { setMenuOpen(!menuOpen); soundFX.click(); }}
        >
          {menuOpen ? "[ CLOSE ]" : "[ MENU ]"}
        </button>

        <div className={`nav-links ${menuOpen ? "open" : ""}`}>
          {links.map((l) => (
            <Link
              key={l.to}
              to={l.to}
              className={`nav-link ${location.pathname === l.to ? "active" : ""}`}
              onMouseEnter={() => soundFX.hover()}
              onClick={() => { soundFX.click(); setMenuOpen(false); }}
            >
              {l.label}
            </Link>
          ))}
        </div>

        <div className="nav-right">
          {user && (
            <>
              <div className="nav-balance" onMouseEnter={() => soundFX.hover()}>
                <span className="balance-label">BALANCE</span>
                <span className="balance-value">{Number(balance).toLocaleString()} Ç</span>
              </div>
              <div className="nav-rank">
                <span className="rank-badge">{user.rank?.toUpperCase()}</span>
              </div>
              <button
                className="logout-btn"
                onClick={() => { soundFX.click(); onLogout(); }}
                onMouseEnter={() => soundFX.hover()}
              >
                LOGOUT
              </button>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}
