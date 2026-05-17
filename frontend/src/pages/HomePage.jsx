import { Link } from "react-router-dom";
import { soundFX } from "../utils/soundFX";
import "./HomePage.css";

export default function HomePage({ isAuthenticated }) {
  return (
    <div className="home-page">
      <div className="hero-section">
        <div className="hero-diamond-wrap">
          <div className="hero-diamond">◆</div>
          <div className="hero-diamond-ring" />
        </div>

        <h1 className="hero-title animate-slide-up">CRYTX</h1>
        <p className="hero-subtitle animate-slide-up">
          THE CRYSTAL EXCHANGE
        </p>
        <p className="hero-lore animate-slide-up">
          After decades of devastating wars and alien invasions, a massive asteroid
          crashed into Earth — carrying mysterious crystals known as <span className="text-glow-cyan">Crytals</span>.
          Now, the elite survivors trade Crytal-backed cards in a ruthless economy.
          <br /><br />
          <span className="text-glow-green">Will you rise from scavenger to sovereign?</span>
        </p>

        <div className="hero-cta animate-slide-up">
          {isAuthenticated ? (
            <Link to="/market" className="btn btn-primary" onMouseEnter={() => soundFX.hover()} onClick={() => soundFX.click()}>
              ENTER THE MARKET
            </Link>
          ) : (
            <>
              <Link to="/signup" className="btn btn-primary" onMouseEnter={() => soundFX.hover()} onClick={() => soundFX.click()}>
                JOIN THE SYNDICATE
              </Link>
              <Link to="/login" className="btn" onMouseEnter={() => soundFX.hover()} onClick={() => soundFX.click()}>
                LOGIN
              </Link>
            </>
          )}
        </div>
      </div>

      <div className="sectors-section animate-slide-up">
        <h2>TRADING SECTORS</h2>
        <div className="sector-grid">
          {[
            { icon: "🌾", name: "AGRIFLUX", desc: "Food supply chain", color: "#39ff14" },
            { icon: "💊", name: "MEDCORE", desc: "Medical resources", color: "#ff00ff" },
            { icon: "⚡", name: "VOLT", desc: "Energy systems", color: "#ffd700" },
            { icon: "🔫", name: "ARSENAL", desc: "Weapons & defense", color: "#ff3333" },
            { icon: "🔧", name: "NEXATECH", desc: "Advanced tech", color: "#00f5e4" },
            { icon: "🏗️", name: "IRONWORKS", desc: "Infrastructure", color: "#b44aff" },
          ].map((s) => (
            <div key={s.name} className="sector-card" style={{ borderColor: s.color }}>
              <span className="sector-icon">{s.icon}</span>
              <span className="sector-name" style={{ color: s.color }}>{s.name}</span>
              <span className="sector-desc">{s.desc}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
