import { useState, useEffect } from "react";
import axios from "axios";
import Card from "../components/Card";
import "./Leaderboard.css";

const API_BASE = "http://127.0.0.1:8001/api/market";

export default function Leaderboard() {
  const [leaderboard, setLeaderboard] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchLeaderboard();
  }, []);

  const fetchLeaderboard = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await axios.get(`${API_BASE}/users-by-networth/`, {
        headers: { Authorization: `Bearer ${localStorage.getItem("access_token")}` },
      });
      setLeaderboard(response.data);
    } catch (err) {
      console.error("Failed to load leaderboard", err);
      setError("Leaderboard feature coming soon. Compete on the market!");
      // Show empty state for now
      setLeaderboard([]);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="leaderboard">
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>Loading leaderboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="leaderboard">
      <div className="leaderboard-header">
        <h1>Leaderboard</h1>
        <p className="subtitle">Top traders by net worth</p>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {leaderboard.length === 0 ? (
        <Card>
          <div className="empty-state">
            <p>Leaderboard feature is under development.</p>
            <p>Keep trading to climb the ranks!</p>
          </div>
        </Card>
      ) : (
        <div className="leaderboard-container">
          {leaderboard.map((player, index) => (
            <Card key={index} hover className={`leaderboard-card rank-${player.rank || index + 1}`}>
              <div className="rank-badge">#{player.rank || index + 1}</div>
              
              <div className="player-info">
                <h3>{player.username || "Anonymous"}</h3>
                <div className="net-worth">
                  <span className="money-tag">CR</span> {(player.net_worth || 0).toLocaleString()}
                </div>
              </div>

              {(player.rank || index + 1) === 1 && <div className="rank-sigil" aria-hidden="true" />}
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
