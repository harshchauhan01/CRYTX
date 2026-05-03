import { useState, useEffect } from "react";
import axios from "axios";
import Card from "../components/Card";
import Button from "../components/Button";
import "./MarketDashboard.css";

const API_BASE = "http://127.0.0.1:8001/api/market";

export default function MarketDashboard({ onBalanceUpdate }) {
  const [assets, setAssets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedAsset, setSelectedAsset] = useState(null);
  const [quantity, setQuantity] = useState(1);
  const [tradeType, setTradeType] = useState("buy");
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchAssets();
    fetchBalance();
  }, []);

  const getVolatilityLabel = (vol) => {
    const pct = Math.round((vol || 0) * 100);
    if (pct >= 15) return { label: "High", cls: "high" };
    if (pct >= 5) return { label: "Medium", cls: "medium" };
    return { label: "Low", cls: "low" };
  };

  const formatChange = (current, base) => {
    const cur = parseFloat(current) || 0;
    const b = parseFloat(base) || 0;
    if (!b) return { pct: 0, cls: "neutral", symbol: "—" };
    const diff = cur - b;
    const pct = (diff / b) * 100;
    if (pct > 0.1) return { pct, cls: "up", symbol: "▲" };
    if (pct < -0.1) return { pct, cls: "down", symbol: "▼" };
    return { pct, cls: "neutral", symbol: "—" };
  };

  const fetchBalance = async () => {
    try {
      const token = localStorage.getItem("access_token");
      const response = await axios.get(`${API_BASE}/holdings/portfolio_value/`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (onBalanceUpdate) {
        onBalanceUpdate(response.data.cash_balance);
      }
    } catch (err) {
      console.error("Failed to fetch balance", err);
    }
  };

  const fetchAssets = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE}/assets/`);
      setAssets(response.data.results || response.data);
    } catch (err) {
      setError("Failed to load assets");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleTradeSubmit = async (e) => {
    e.preventDefault();
    if (!selectedAsset) return;

    // Validation
    const qty = parseFloat(quantity);
    if (!qty || qty <= 0) {
      setError("Please enter a valid quantity");
      return;
    }

    try {
      setError(null);
      const token = localStorage.getItem("access_token");
      
      if (!token) {
        setError("Authentication token missing. Please log in again.");
        return;
      }

      const response = await axios.post(
        `${API_BASE}/orders/`,
        {
          asset_id: selectedAsset.id,
          quantity: qty,
          side: tradeType,
        },
        {
          headers: { 
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        }
      );

      setError(null);
      setSelectedAsset(null);
      setQuantity(1);
      fetchAssets();
      fetchBalance();
      alert(`${tradeType.toUpperCase()} order placed successfully!`);
    } catch (err) {
      const errorMsg = err.response?.data?.error ||
                       err.response?.data?.detail ||
                       err.message ||
                       "Trade failed. Please try again.";
      setError(errorMsg);
      console.error("Trade error:", err);
    }
  };

  if (loading) {
    return (
      <div className="market-dashboard">
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>Loading markets...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="market-dashboard">
      <div className="dashboard-header">
        <h1>Crystal Markets</h1>
        <p className="subtitle">Trade crystal-backed assets and build your wealth</p>
      </div>

      {error && <div className="error-banner">{error}</div>}

      <div className="assets-grid">
        {assets.map((asset) => {
          const volPercent = Math.round((asset.volatility || 0) * 100);
          const volMeta = getVolatilityLabel(asset.volatility || 0);
          const priceChange = formatChange(asset.current_price, asset.base_price);
          const supplyPressure = asset.supply > asset.demand ? 'oversupply' : (asset.demand > asset.supply ? 'highdemand' : 'balanced');
          const volBg = volMeta.cls === 'high' ? 'linear-gradient(90deg,#ff8a80,#ff5252)' : (volMeta.cls === 'medium' ? 'linear-gradient(90deg,#ffd86b,#ffb74d)' : 'linear-gradient(90deg,#6cff7d,#8ef0a6)');

          return (
            <Card key={asset.id} hover className="asset-card">
              <div className="card-header">
                <h3 className="card-title">{asset.name}</h3>
                <span className="card-badge">{asset.category_name}</span>
              </div>

              <div className="card-body">
                <div className="card-price">
                  <span className="money-tag">CR</span>
                  <span className="price-value">{parseFloat(asset.current_price).toFixed(2)}</span>
                  <span className={`price-change ${priceChange.cls}`}>
                    {priceChange.symbol} {Math.abs(priceChange.pct).toFixed(1)}%
                  </span>
                </div>

                <div className="card-stats">
                  <div className={`stat ${supplyPressure === 'oversupply' ? 'oversupply' : (supplyPressure === 'highdemand' ? 'highdemand' : 'balanced')}`}>
                    <div className="stat-label">Supply</div>
                    <div className="stat-value">
                      {asset.supply.toLocaleString()}
                      {supplyPressure === 'oversupply' ? <span className="stat-arrow"> ▼</span> : (supplyPressure === 'highdemand' ? <span className="stat-arrow"> ▲</span> : null)}
                    </div>
                  </div>
                  <div className={`stat ${supplyPressure === 'highdemand' ? 'highdemand' : (supplyPressure === 'oversupply' ? 'oversupply' : 'balanced')}`}>
                    <div className="stat-label">Demand</div>
                    <div className="stat-value">
                      {asset.demand.toLocaleString()}
                      {supplyPressure === 'highdemand' ? <span className="stat-arrow"> ▲</span> : (supplyPressure === 'oversupply' ? <span className="stat-arrow"> ▼</span> : null)}
                    </div>
                  </div>
                </div>

                <div className="volatility-meter">
                  <div className="label">Volatility: {volPercent}% — <span className={`vol-label ${volMeta.cls}`}>{volMeta.label}</span></div>
                  <div className="meter" style={{ background: volBg }}>
                    <div className="fill" style={{ width: `${volPercent}%`, opacity: 1 }}></div>
                  </div>
                </div>
              </div>

              <div className="card-footer">
                <Button
                  variant="primary"
                  size="sm"
                  fullWidth
                  onClick={() => {
                    setSelectedAsset(asset);
                    setTradeType("buy");
                  }}
                >
                  Buy
                </Button>
                <Button
                  variant="secondary"
                  size="sm"
                  fullWidth
                  onClick={() => {
                    setSelectedAsset(asset);
                    setTradeType("sell");
                  }}
                >
                  Sell
                </Button>
              </div>
            </Card>
          );
        })}
      </div>

      {selectedAsset && (
        <div className="modal-overlay" onClick={() => setSelectedAsset(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <button className="modal-close" onClick={() => setSelectedAsset(null)}>✕</button>

            <h2>
              {tradeType === "buy" ? "Buy" : "Sell"} {selectedAsset.name}
            </h2>

            {error && <div className="modal-error-banner">{error}</div>}

            <form onSubmit={handleTradeSubmit}>
              <div className="form-group">
                <label>Quantity</label>
                <input
                  type="number"
                  min="0.1"
                  step="0.1"
                  value={quantity}
                  onChange={(e) => setQuantity(e.target.value)}
                  required
                />
              </div>

              <div className="form-group">
                <label>Price per unit</label>
                <input
                  type="text"
                  value={`CR ${parseFloat(selectedAsset.current_price).toFixed(2)}`}
                  disabled
                />
              </div>

              <div className="form-group">
                <label>Total cost</label>
                <input
                  type="text"
                  value={`CR ${(quantity * selectedAsset.current_price).toFixed(2)}`}
                  disabled
                />
              </div>

              <Button
                variant={tradeType === "buy" ? "success" : "danger"}
                size="lg"
                fullWidth
                type="submit"
              >
                {tradeType === "buy" ? "Confirm Buy" : "Confirm Sell"}
              </Button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
