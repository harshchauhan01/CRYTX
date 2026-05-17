import { useState, useEffect, useMemo } from "react";
import api from "../utils/api";
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";
import { soundFX } from "../utils/soundFX";
import { toast } from "../components/Toast";
import "./MarketDashboard.css";

export default function MarketDashboard({ onTradeComplete }) {
  const [assets, setAssets] = useState([]);
  const [selected, setSelected] = useState(null);
  const [history, setHistory] = useState([]);
  const [tradeType, setTradeType] = useState("BUY");
  const [qty, setQty] = useState("");
  const [loading, setLoading] = useState(true);
  const [trading, setTrading] = useState(false);

  useEffect(() => { fetchAssets(); }, []);

  const fetchAssets = async () => {
    try {
      const res = await api.get("/market/assets/");
      setAssets(res.data.results || res.data);
    } catch (err) {
      toast("Failed to load market data", "error");
    } finally {
      setLoading(false);
    }
  };

  const selectAsset = async (asset) => {
    soundFX.click();
    setSelected(asset);
    setQty("");
    try {
      const res = await api.get(`/market/assets/${asset.id}/history/?limit=50`);
      setHistory(res.data);
    } catch {
      setHistory([]);
    }
  };

  const executeTrade = async () => {
    if (!selected || !qty || Number(qty) <= 0) return;
    soundFX.click();
    setTrading(true);
    try {
      const res = await api.post("/market/trade/", {
        asset_id: selected.id,
        quantity: Number(qty),
        trade_type: tradeType,
      });
      if (tradeType === "BUY") soundFX.buy(); else soundFX.sell();
      toast(
        `${tradeType} ${qty}x ${selected.ticker} @ ${Number(res.data.price).toFixed(2)} Ç`,
        "success"
      );
      setQty("");
      fetchAssets();
      if (onTradeComplete) onTradeComplete();
    } catch (err) {
      soundFX.error();
      toast(err.response?.data?.error || "Trade failed", "error");
    } finally {
      setTrading(false);
    }
  };

  const chartData = useMemo(() => {
    return history.map((h) => ({
      time: new Date(h.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      price: Number(h.price),
    }));
  }, [history]);

  const previewCost = useMemo(() => {
    if (!selected || !qty || Number(qty) <= 0) return null;
    return (Number(selected.current_price) * Number(qty)).toFixed(2);
  }, [selected, qty]);

  if (loading) {
    return (
      <div className="dashboard-loading">
        <div className="loading-diamond animate-pulse">◆</div>
        <p className="font-pixel" style={{ fontSize: 10, color: "var(--cyan)" }}>
          LOADING MARKET DATA...
        </p>
      </div>
    );
  }

  return (
    <div className="market-dashboard">
      <div className="exchange-header">
        <div>
          <p className="exchange-label">CRYTX</p>
          <h1 className="exchange-title">TRADING FLOOR</h1>
        </div>
        <div className="exchange-stats">
          <div className="stat-box">
            <span className="stat-label">ASSETS</span>
            <span className="stat-value text-glow-cyan">{assets.length}</span>
          </div>
          <div className="stat-box">
            <span className="stat-label">VOLUME</span>
            <span className="stat-value text-glow-green">
              {assets.reduce((s, a) => s + a.buy_volume + a.sell_volume, 0).toLocaleString()}
            </span>
          </div>
        </div>
      </div>

      <div className="exchange-body">
        {/* Left: Asset Table */}
        <div className="exchange-left">
          <table className="asset-table">
            <thead>
              <tr>
                <th>CARD</th>
                <th>SECTOR</th>
                <th>PRICE</th>
                <th>CHANGE</th>
                <th>ACTION</th>
              </tr>
            </thead>
            <tbody>
              {assets.map((a) => (
                <tr
                  key={a.id}
                  className={selected?.id === a.id ? "selected" : ""}
                  onClick={() => selectAsset(a)}
                  onMouseEnter={() => soundFX.hover()}
                >
                  <td className="asset-name-cell">
                    <span className="asset-icon">{a.category_icon}</span>
                    <div>
                      <div className="asset-ticker">{a.ticker}</div>
                      <div className="asset-fullname">{a.name}</div>
                    </div>
                  </td>
                  <td>
                    <span className="sector-tag" style={{ color: a.category_color }}>
                      {a.category_name}
                    </span>
                  </td>
                  <td className="price-cell font-mono">
                    {Number(a.current_price).toFixed(2)} Ç
                  </td>
                  <td className={`change-cell font-mono ${a.change_pct >= 0 ? "positive" : "negative"}`}>
                    {a.change_pct >= 0 ? "+" : ""}{a.change_pct.toFixed(2)}%
                  </td>
                  <td>
                    <button
                      className="btn btn-buy btn-sm"
                      onClick={(e) => { e.stopPropagation(); selectAsset(a); setTradeType("BUY"); }}
                    >
                      BUY
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Right: Trade Panel */}
        <div className="exchange-right">
          {!selected ? (
            <div className="no-selection">
              <div className="ns-diamond animate-pulse">◆</div>
              <p className="font-pixel" style={{ fontSize: 10, color: "var(--muted)" }}>
                SELECT A CARD TO TRADE
              </p>
            </div>
          ) : (
            <div className="trade-panel">
              <div className="tp-header">
                <span className="tp-icon">{selected.category_icon}</span>
                <div>
                  <h3 className="tp-ticker">{selected.ticker}</h3>
                  <p className="tp-name">{selected.name}</p>
                </div>
                <div className="tp-price">
                  <span className="font-mono" style={{ fontSize: 24, color: "var(--cyan)", textShadow: "var(--glow-cyan)" }}>
                    {Number(selected.current_price).toFixed(2)}
                  </span>
                  <span className="font-pixel" style={{ fontSize: 8, color: "var(--muted)" }}>Ç / UNIT</span>
                </div>
              </div>

              {/* Chart */}
              {chartData.length > 0 && (
                <div className="tp-chart">
                  <ResponsiveContainer width="100%" height={180}>
                    <LineChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#0c2a3f" />
                      <XAxis dataKey="time" tick={{ fill: "#5a6a7a", fontSize: 10 }} />
                      <YAxis domain={["auto", "auto"]} tick={{ fill: "#5a6a7a", fontSize: 10 }} />
                      <Tooltip
                        contentStyle={{ background: "#05111c", border: "1px solid #0c2a3f", color: "#e0e0e0", fontSize: 12 }}
                      />
                      <Line type="monotone" dataKey="price" stroke="#00f5e4" strokeWidth={2} dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              )}

              {/* Trade Form */}
              <div className="tp-form">
                <div className="tp-type-toggle">
                  <button
                    className={`btn ${tradeType === "BUY" ? "btn-buy active" : ""}`}
                    onClick={() => { setTradeType("BUY"); soundFX.click(); }}
                  >
                    BUY
                  </button>
                  <button
                    className={`btn ${tradeType === "SELL" ? "btn-sell active" : ""}`}
                    onClick={() => { setTradeType("SELL"); soundFX.click(); }}
                  >
                    SELL
                  </button>
                </div>

                <div className="tp-qty-row">
                  <label className="font-pixel" style={{ fontSize: 8, color: "var(--muted)" }}>QUANTITY</label>
                  <input
                    className="input"
                    type="number"
                    min="0"
                    step="1"
                    placeholder="0"
                    value={qty}
                    onChange={(e) => setQty(e.target.value)}
                  />
                </div>

                {previewCost && (
                  <div className="tp-preview">
                    <span className="font-pixel" style={{ fontSize: 8, color: "var(--muted)" }}>
                      EST. {tradeType === "BUY" ? "COST" : "REVENUE"}
                    </span>
                    <span className="font-mono" style={{ fontSize: 18, color: "var(--yellow)" }}>
                      {previewCost} Ç
                    </span>
                  </div>
                )}

                <button
                  className={`btn ${tradeType === "BUY" ? "btn-buy" : "btn-sell"} tp-execute`}
                  onClick={executeTrade}
                  disabled={trading || !qty || Number(qty) <= 0}
                >
                  {trading ? "EXECUTING..." : `${tradeType} ${selected.ticker}`}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
