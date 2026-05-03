import { useState, useEffect } from "react";
import axios from "axios";
import "./Leaderboard.css";

const API_BASE = "http://127.0.0.1:8001/api/market";

function fmtVal(v) {
  const n = parseFloat(v) || 0;
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(2) + "M";
  if (n >= 1_000)     return (n / 1_000).toFixed(1) + "K";
  return n.toFixed(0);
}

export default function Leaderboard() {
  const [rows,    setRows]    = useState([]);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState(null);

  useEffect(() => { fetchData(); }, []);

  const fetchData = async () => {
    try {
      setLoading(true); setError(null);
      const token = localStorage.getItem("access_token");
      const r = await axios.get(`${API_BASE}/users-by-networth/`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setRows(r.data);
    } catch {
      setError("Leaderboard data unavailable. Keep trading to climb the ranks!");
      setRows([]);
    } finally { setLoading(false); }
  };

  const totalVol     = rows.reduce((s, r) => s + (r.net_worth || 0), 0);
  const activeTraders = rows.length;

  if (loading) return <div className="leaderboard-page"><div className="px-loader">LOADING BARONS...</div></div>;

  return (
    <div className="leaderboard-page">
      <div className="section-label">LDR / 03</div>
      <h1 className="page-title">TOP CRYSTAL BARONS</h1>

      {error && <div className="px-info">▶ {error}</div>}

      {rows.length === 0 ? (
        <div className="px-info">No traders ranked yet — be the first to dominate.</div>
      ) : (
        <>
          <table className="lb-table panel-border">
            <thead>
              <tr>
                <th>RANK</th>
                <th>TRADER</th>
                <th>NET WORTH</th>
                <th>Δ</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((p, i) => {
                const rank = p.rank || i + 1;
                const worth = p.net_worth || 0;
                const change = Math.random() > 0.4; // visual only
                return (
                  <tr key={i}>
                    <td>
                      <span className={`lb-rank ${rank <= 3 ? `rank-${rank}` : ""}`}>
                        #{String(rank).padStart(2, "0")}
                      </span>
                    </td>
                    <td>
                      <span className="lb-username">
                        <span className="lb-avatar" />
                        {(p.username || "ANONYMOUS").toUpperCase()}
                      </span>
                    </td>
                    <td>
                      <span className="lb-networth">◆ {fmtVal(worth)}</span>
                    </td>
                    <td>
                      <span className={change ? "lb-trend-up" : "lb-trend-down"}>
                        {change ? "▲" : "▼"}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>

          <div className="lb-stats-strip panel-border">
            <div className="lb-stat-box">
              <div className="lb-stat-label">TOTAL VOL 24H</div>
              <div className="lb-stat-val green">◆ {fmtVal(totalVol)}</div>
            </div>
            <div className="lb-stat-box">
              <div className="lb-stat-label">ACTIVE TRADERS</div>
              <div className="lb-stat-val cyan">{activeTraders}</div>
            </div>
            <div className="lb-stat-box">
              <div className="lb-stat-label">TOP WORTH</div>
              <div className="lb-stat-val orange">◆ {fmtVal(rows[0]?.net_worth || 0)}</div>
            </div>
            <div className="lb-stat-box">
              <div className="lb-stat-label">SURVIVORS</div>
              <div className="lb-stat-val white">{(activeTraders * 1247).toLocaleString()}</div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
