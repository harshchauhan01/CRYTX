import { useState, useEffect } from "react";
import axios from "axios";
import Card from "../components/Card";
import "./Portfolio.css";

const API_BASE = "http://127.0.0.1:8001/api/market";

export default function Portfolio({ onBalanceUpdate }) {
  const [holdings, setHoldings] = useState([]);
  const [portfolioValue, setPortfolioValue] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchPortfolio();
  }, []);

  const fetchPortfolio = async () => {
    try {
      setLoading(true);
      setError(null);
      const token = localStorage.getItem("access_token");
      
      if (!token) {
        setError("Authentication required. Please log in.");
        return;
      }
      
      const [holdingsRes, valueRes] = await Promise.all([
        axios.get(`${API_BASE}/holdings/`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
        axios.get(`${API_BASE}/holdings/portfolio_value/`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
      ]);

      setHoldings(holdingsRes.data.results || holdingsRes.data);
      setPortfolioValue(valueRes.data);
      
      // Update balance in navbar
      if (onBalanceUpdate && valueRes.data) {
        onBalanceUpdate(valueRes.data.cash_balance);
      }
    } catch (err) {
      console.error("Failed to load portfolio", err);
      setError(err.response?.data?.error || err.message || "Failed to load portfolio");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="portfolio">
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>Loading portfolio...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="portfolio">
      <div className="portfolio-header">
        <h1>Your Portfolio</h1>
        <p className="subtitle">Manage your crystal-backed assets</p>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {portfolioValue && (
        <div className="portfolio-summary">
          <Card>
            <div className="summary-grid">
              <div className="summary-item">
                <div className="summary-label">Holdings Value</div>
                <div className="summary-value">
                  <span className="money-tag">CR</span> {portfolioValue.total_holdings_value.toFixed(2)}
                </div>
              </div>
              <div className="summary-item">
                <div className="summary-label">Cash Balance</div>
                <div className="summary-value">
                  <span className="money-tag">CR</span> {portfolioValue.cash_balance.toFixed(2)}
                </div>
              </div>
              <div className="summary-item highlight">
                <div className="summary-label">Net Worth</div>
                <div className="summary-value">
                  <span className="money-tag">CR</span> {portfolioValue.net_worth.toFixed(2)}
                </div>
              </div>
            </div>
          </Card>
        </div>
      )}

      <div className="holdings-section">
        <h2>Your Holdings</h2>
        
        {holdings.length === 0 ? (
          <Card>
            <div className="empty-state">
              <p>You don't own any assets yet.</p>
              <p>Visit the Market to start trading!</p>
            </div>
          </Card>
        ) : (
          <div className="holdings-list">
            {holdings.map((holding) => (
              <Card key={holding.id} hover className="holding-card">
                <div className="holding-header">
                  <h3>{holding.asset_name}</h3>
                  <span className="quantity-badge">{holding.quantity}</span>
                </div>
                
                <div className="holding-details">
                  <div className="detail-item">
                    <span className="label">Current Price:</span>
                    <span className="value"><span className="money-tag">CR</span> {parseFloat(holding.asset_price).toFixed(2)}</span>
                  </div>
                  <div className="detail-item">
                    <span className="label">Avg Buy Price:</span>
                    <span className="value"><span className="money-tag">CR</span> {parseFloat(holding.avg_price).toFixed(2)}</span>
                  </div>
                  <div className="detail-item">
                    <span className="label">Total Value:</span>
                    <span className="value highlight"><span className="money-tag">CR</span> {parseFloat(holding.value).toFixed(2)}</span>
                  </div>
                  <div className="detail-item">
                    <span className="label">Profit/Loss:</span>
                    <span className={`value ${parseFloat(holding.value) - (holding.quantity * holding.avg_price) > 0 ? "profit" : "loss"}`}>
                      <span className="money-tag">CR</span> {(parseFloat(holding.value) - (holding.quantity * holding.avg_price)).toFixed(2)}
                    </span>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
