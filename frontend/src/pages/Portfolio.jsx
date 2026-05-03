import { useState, useEffect } from "react";
import axios from "axios";
import "./Portfolio.css";

const API_BASE = "http://127.0.0.1:8001/api/market";

export default function Portfolio({ onBalanceUpdate }) {
  const [holdings, setHoldings]         = useState([]);
  const [portfolioValue, setPortfolioValue] = useState(null);
  const [loading, setLoading]           = useState(true);
  const [error, setError]               = useState(null);

  useEffect(() => { fetchPortfolio(); }, []);

  const fetchPortfolio = async () => {
    try {
      setLoading(true); setError(null);
      const token = localStorage.getItem("access_token");
      if (!token) { setError("Authentication required."); return; }

      const [hRes, vRes] = await Promise.all([
        axios.get(`${API_BASE}/portfolios/`,              { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API_BASE}/portfolios/portfolio_value/`, { headers: { Authorization: `Bearer ${token}` } }),
      ]);
      setHoldings(hRes.data.results || hRes.data);
      setPortfolioValue(vRes.data);
      if (onBalanceUpdate && vRes.data) onBalanceUpdate(vRes.data.cash_balance);
    } catch (err) {
      setError(err.response?.data?.error || err.message || "Failed to load portfolio");
    } finally { setLoading(false); }
  };

  if (loading) return <div className="portfolio-page"><div className="px-loader">LOADING HOLDINGS...</div></div>;

  return (
    <div className="portfolio-page">
      <div className="section-label">PRT / 02</div>
      <h1 className="page-title">YOUR HOLDINGS</h1>

      {error && <div className="px-error">▶ {error}</div>}

      {portfolioValue && (
        <div className="portfolio-summary panel-border">
          <div className="summary-block">
            <div className="summary-block-label">HOLDINGS VALUE</div>
            <div className="summary-block-value sv-hold">
              <span className="sym">◆</span>
              {parseFloat(portfolioValue.total_portfolios_value).toLocaleString("en-US", { minimumFractionDigits: 2 })}
            </div>
          </div>
          <div className="summary-block">
            <div className="summary-block-label">CASH BALANCE</div>
            <div className="summary-block-value sv-cash">
              <span className="sym">◆</span>
              {parseFloat(portfolioValue.cash_balance).toLocaleString("en-US", { minimumFractionDigits: 2 })}
            </div>
          </div>
          <div className="summary-block highlight">
            <div className="summary-block-label">NET WORTH</div>
            <div className="summary-block-value sv-net">
              <span className="sym">◆</span>
              {parseFloat(portfolioValue.net_worth).toLocaleString("en-US", { minimumFractionDigits: 2 })}
            </div>
          </div>
        </div>
      )}

      {holdings.length === 0 ? (
        <div className="portfolio-empty">
          <span className="portfolio-empty-icon">◆</span>
          <div className="portfolio-empty-title">NO ACTIVE POSITIONS</div>
          <div className="portfolio-empty-sub">Visit the Market to acquire assets and build your syndicate.</div>
        </div>
      ) : (
        <table className="holdings-table panel-border">
          <thead>
            <tr>
              <th>ASSET</th>
              <th>QTY</th>
              <th>CURRENT PRICE</th>
              <th>AVG BUY</th>
              <th>TOTAL VALUE</th>
              <th>P / L</th>
            </tr>
          </thead>
          <tbody>
            {holdings.map(h => {
              const qty   = parseFloat(h.quantity)      || 0;
              const cur   = parseFloat(h.asset_price)   || 0;
              const avg   = parseFloat(h.avg_buy_price) || 0;
              const val   = qty * cur;
              const cost  = qty * avg;
              const pnl   = val - cost;
              const isPos = pnl >= 0;
              return (
                <tr key={h.id}>
                  <td><span className="holding-name">{(h.asset_name || "UNKNOWN").toUpperCase()}</span></td>
                  <td><span className="holding-qty">{qty.toLocaleString()}</span></td>
                  <td><span className="holding-price">◆ {cur.toFixed(2)}</span></td>
                  <td><span className="holding-avg">◆ {avg.toFixed(2)}</span></td>
                  <td><span className="holding-value">◆ {val.toFixed(2)}</span></td>
                  <td>
                    <span className={isPos ? "holding-pnl-pos" : "holding-pnl-neg"}>
                      {isPos ? "▲" : "▼"} ◆ {Math.abs(pnl).toFixed(2)}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </div>
  );
}
