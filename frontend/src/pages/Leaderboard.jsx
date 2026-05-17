import { useState, useEffect } from "react";
import api from "../utils/api";
import "./Leaderboard.css";

export default function Leaderboard() {
  const [players, setPlayers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/market/leaderboard/")
      .then((res) => setPlayers(res.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="lb-loading">
        <div className="loading-diamond animate-pulse">◆</div>
        <p className="font-pixel" style={{ fontSize: 10, color: "var(--cyan)" }}>LOADING RANKINGS...</p>
      </div>
    );
  }

  const medals = ["👑", "🥈", "🥉"];

  return (
    <div className="leaderboard-page">
      <div className="lb-header">
        <div>
          <p className="lb-label">GLOBAL</p>
          <h1 className="lb-title">LEADERBOARD</h1>
        </div>
        <p className="lb-sub">TOP CRYSTAL BARONS BY NET WORTH</p>
      </div>

      {players.length === 0 ? (
        <div className="lb-empty">
          <p className="font-pixel" style={{ fontSize: 10, color: "var(--muted)" }}>NO PLAYERS YET</p>
        </div>
      ) : (
        <table className="lb-table panel-border">
          <thead>
            <tr>
              <th>#</th>
              <th>PLAYER</th>
              <th>RANK</th>
              <th>NET WORTH</th>
              <th>TRADES</th>
            </tr>
          </thead>
          <tbody>
            {players.map((p, i) => (
              <tr key={p.username} className={i < 3 ? `top-${i + 1}` : ""}>
                <td className="lb-rank font-mono">
                  {i < 3 ? <span className="medal">{medals[i]}</span> : p.rank}
                </td>
                <td className="lb-username">{p.username}</td>
                <td>
                  <span className="lb-player-rank">{p.player_rank?.toUpperCase()}</span>
                </td>
                <td className="lb-networth font-mono text-glow-cyan">
                  {Number(p.net_worth).toLocaleString(undefined, { minimumFractionDigits: 2 })} Ç
                </td>
                <td className="font-mono" style={{ color: "var(--muted)" }}>
                  {p.total_trades}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
