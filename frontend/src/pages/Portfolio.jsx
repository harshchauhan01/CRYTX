import { useState, useEffect } from "react";
import api from "../utils/api";
import "./Portfolio.css";

export default function Portfolio() {
  const [holdings, setHoldings] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => { fetchData(); }, []);

  const fetchData = async () => {
    try {
      const [hRes, vRes] = await Promise.all([
        api.get("/market/portfolio/"),
        api.get("/market/portfolio/value/"),
      ]);
      setHoldings(hRes.data.results || hRes.data);
      setSummary(vRes.data);
    } catch {} finally { setLoading(false); }
  };

  if (loading) {
    return (
      <div className="portfolio-loading">
        <div className="loading-diamond animate-pulse">◆</div>
        <p className="font-pixel" style={{ fontSize: 10, color: "var(--cyan)" }}>LOADING PORTFOLIO...</p>
      </div>
    );
  }

  const totalPL = holdings.reduce((s, h) => s + (h.profit_loss || 0), 0);

  return (
    <div className="portfolio-page">
      <div className="portfolio-header">
        <div>
          <p className="portfolio-label">YOUR</p>
          <h1 className="portfolio-title">PORTFOLIO</h1>
        </div>
      </div>

      {summary && (
        <div className="portfolio-summary">
          <div className="summary-card">
            <span className="sc-label">NET WORTH</span>
            <span className="sc-value text-glow-cyan">{Number(summary.net_worth).toLocaleString(undefined, { minimumFractionDigits: 2 })} Ç</span>
          </div>
          <div className="summary-card">
            <span className="sc-label">PORTFOLIO VALUE</span>
            <span className="sc-value text-glow-green">{Number(summary.portfolio_value).toLocaleString(undefined, { minimumFractionDigits: 2 })} Ç</span>
          </div>
          <div className="summary-card">
            <span className="sc-label">WALLET</span>
            <span className="sc-value" style={{ color: "var(--yellow)" }}>{Number(summary.wallet_balance).toLocaleString(undefined, { minimumFractionDigits: 2 })} Ç</span>
          </div>
          <div className="summary-card">
            <span className="sc-label">P&L</span>
            <span className={`sc-value ${totalPL >= 0 ? "text-glow-green" : "text-glow-red"}`}>
              {totalPL >= 0 ? "+" : ""}{totalPL.toFixed(2)} Ç
            </span>
          </div>
        </div>
      )}

      {holdings.length === 0 ? (
        <div className="empty-portfolio">
          <p className="font-pixel" style={{ fontSize: 10, color: "var(--muted)" }}>
            NO HOLDINGS YET. VISIT THE TRADING FLOOR.
          </p>
        </div>
      ) : (
        <table className="holdings-table panel-border">
          <thead>
            <tr>
              <th>CARD</th>
              <th>QTY</th>
              <th>AVG BUY</th>
              <th>CURRENT</th>
              <th>VALUE</th>
              <th>P&L</th>
            </tr>
          </thead>
          <tbody>
            {holdings.map((h) => (
              <tr key={h.id}>
                <td className="holding-name">
                  <span style={{ fontSize: 18 }}>{h.category_icon}</span>
                  <div>
                    <div className="font-mono" style={{ fontWeight: 600 }}>{h.asset_ticker}</div>
                    <div style={{ fontSize: 11, color: "var(--muted)" }}>{h.asset_name}</div>
                  </div>
                </td>
                <td className="font-mono">{Number(h.quantity).toFixed(1)}</td>
                <td className="font-mono">{Number(h.avg_buy_price).toFixed(2)} Ç</td>
                <td className="font-mono">{Number(h.asset_price).toFixed(2)} Ç</td>
                <td className="font-mono" style={{ color: "var(--cyan)" }}>{Number(h.current_value).toFixed(2)} Ç</td>
                <td className={`font-mono ${h.profit_loss >= 0 ? "positive" : "negative"}`}>
                  {h.profit_loss >= 0 ? "+" : ""}{Number(h.profit_loss).toFixed(2)} Ç
                  <span style={{ fontSize: 11, marginLeft: 6 }}>
                    ({h.profit_loss_pct >= 0 ? "+" : ""}{Number(h.profit_loss_pct).toFixed(1)}%)
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
