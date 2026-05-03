import { useState, useEffect, useMemo } from "react";
import axios from "axios";
import { ResponsiveContainer, LineChart, Line, YAxis } from "recharts";
import { soundFX } from "../utils/soundFX";
import "./MarketDashboard.css";

const API_BASE = "http://127.0.0.1:8001/api/market";
const ICONS = { Food:"🌾", Air:"💨", Medical:"💊", Energy:"⚡", Water:"💧", Ammo:"🎯", default:"◆" };

function fmtVal(v) {
  const n = parseFloat(v)||0;
  if(n>=1_000_000) return (n/1_000_000).toFixed(2)+"M";
  if(n>=1_000)     return (n/1_000).toFixed(1)+"K";
  return n.toFixed(2);
}

function PctChange({ current, base }) {
  const cur=parseFloat(current)||0, b=parseFloat(base)||0;
  if(!b) return null;
  const pct=((cur-b)/b)*100, up=pct>=0;
  return <span className={up?"at-chg-up":"at-chg-down"}>{up?"▲":"▼"} {Math.abs(pct).toFixed(1)}%</span>;
}

export default function MarketDashboard({ onBalanceUpdate }) {
  const [assets,    setAssets]    = useState([]);
  const [holdings,  setHoldings]  = useState({});
  const [selected,  setSelected]  = useState(null);
  const [history,   setHistory]   = useState([]);
  const [side,      setSide]      = useState("buy");
  const [qty,       setQty]       = useState(1);
  const [cash,      setCash]      = useState(null);
  const [ordersQ,   setOrdersQ]   = useState(0);
  const [loading,   setLoading]   = useState(true);
  const [tradeMsg,  setTradeMsg]  = useState(null);
  const [tradeErr,  setTradeErr]  = useState(null);
  const [executing, setExecuting] = useState(false);

  useEffect(() => { fetchAll(); }, []);

  useEffect(() => {
    if (!selected) return;
    const fetchHist = async () => {
      try {
        const res = await axios.get(`${API_BASE}/assets/${selected.id}/history/`);
        setHistory(res.data);
      } catch (err) { console.error(err); }
    };
    fetchHist();
    const interval = setInterval(fetchHist, 10000); // Poll chart every 10s
    return () => clearInterval(interval);
  }, [selected?.id]);

  const fetchAll = async () => {
    const token = localStorage.getItem("access_token");
    try {
      setLoading(true);
      const [ar, pr, vr] = await Promise.all([
        axios.get(`${API_BASE}/assets/`),
        axios.get(`${API_BASE}/portfolios/`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API_BASE}/portfolios/portfolio_value/`, { headers: { Authorization: `Bearer ${token}` } }),
      ]);
      const assetList = ar.data.results || ar.data;
      setAssets(assetList);

      // Build holdings map
      const hmap = {};
      (pr.data.results || pr.data).forEach(h => { hmap[h.asset_id || h.asset] = h.quantity; });
      setHoldings(hmap);

      if(vr.data) {
        setCash(parseFloat(vr.data.cash_balance));
        if(onBalanceUpdate) onBalanceUpdate(vr.data.cash_balance);
      }

      const tr = await axios.get(`${API_BASE}/transactions/`, { headers: { Authorization: `Bearer ${token}` } });
      setOrdersQ((tr.data.results || tr.data).length);
    } catch {}
    finally { setLoading(false); }
  };

  const openPanel = (asset, s="buy") => {
    soundFX.blip();
    setSelected(asset); setSide(s); setQty(1); setTradeMsg(null); setTradeErr(null); setHistory([]);
  };

  const changeQty = (delta) => {
    soundFX.blip();
    setQty(q => Math.max(0.1, parseFloat((parseFloat(q) + delta).toFixed(2))));
  };

  const executeTrade = async () => {
    if (!selected || qty <= 0) return;
    setExecuting(true); setTradeMsg(null); setTradeErr(null);
    try {
      const token = localStorage.getItem("access_token");
      await axios.post(
        `${API_BASE}/transactions/`,
        { asset_id: selected.id, quantity: qty, side },
        { headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json", "Idempotency-Key": crypto.randomUUID() } }
      );
      setTradeMsg(`${side.toUpperCase()} ORDER EXECUTED ✔`);
      setOrdersQ(q => q+1);
      await fetchAll();
      setSelected(asst => assets.find(a => a.id === asst?.id) || asst);
      soundFX.execute();
    } catch(err) {
      soundFX.error();
      setTradeErr(err.response?.data?.error || err.response?.data?.detail || "Trade failed");
    } finally { setExecuting(false); }
  };

  const totalHeld = useMemo(() => Object.values(holdings).reduce((s,v)=>s+parseFloat(v||0),0), [holdings]);
  const totalVol  = useMemo(() => assets.reduce((s,a)=>s+parseFloat(a.buy_volume||0)+parseFloat(a.sell_volume||0),0), [assets]);
  const selAsset  = useMemo(() => selected ? assets.find(a=>a.id===selected.id)||selected : null, [selected, assets]);
  const cost      = useMemo(() => (parseFloat(qty)||0) * parseFloat(selAsset?.current_price||0), [qty, selAsset]);

  if(loading) return (
    <div className="exchange-page" style={{alignItems:"center",justifyContent:"center"}}>
      <div className="px-loader">LOADING EXCHANGE FLOOR...</div>
    </div>
  );

  return (
    <div className="exchange-page">
      <div className="exchange-container">
        {/* Sub-header */}
        <div className="exchange-header">
        <div className="exchange-header-label">MKT / LIVE</div>
        <div className="exchange-header-title"><span style={{color:"var(--cyan)"}}>EXCHANGE</span> <span style={{color:"var(--white)"}}>FLOOR</span></div>
        <div className="exchange-header-sub">Buy low, sell loud. Prices tick every 10s.</div>
      </div>

      {/* Ticker */}
      <div className="ex-ticker-wrap">
        <div className="ex-ticker-track">
          {[...assets,...assets].map((a,i)=>{
            const pct=parseFloat(a.base_price)?((parseFloat(a.current_price)-parseFloat(a.base_price))/parseFloat(a.base_price))*100:0;
            const up=pct>=0;
            return(
              <span key={i} className="ex-tick-item">
                {ICONS[a.category_name]||"◆"}
                <span className="ex-tick-name">{a.name.substring(0,4).toUpperCase()}</span>
                <span className="ex-tick-price">◆{parseFloat(a.current_price).toFixed(2)}</span>
                <span className={up?"ex-tick-up":"ex-tick-down"}>{up?"▲":"▼"}{Math.abs(pct).toFixed(1)}%</span>
                <span style={{color:"var(--border)",margin:"0 8px"}}>|</span>
              </span>
            );
          })}
        </div>
      </div>

      {/* Stat boxes */}
      <div className="exchange-stats">
        <div className="ex-stat-box">
          <div className="ex-stat-label">CRYSTAL WALLET</div>
          <div className="ex-stat-val">◆ {cash!=null ? fmtVal(cash) : "—"}</div>
        </div>
        <div className="ex-stat-box">
          <div className="ex-stat-label">VAULT HOLDINGS</div>
          <div className="ex-stat-val green">{totalHeld.toFixed(0)} units</div>
        </div>
        <div className="ex-stat-box">
          <div className="ex-stat-label">ORDERS FILLED</div>
          <div className="ex-stat-val">{ordersQ}</div>
        </div>
      </div>

      {/* Split body */}
      <div className="exchange-body">
        {/* LEFT: asset table */}
        <div className="exchange-left">
          <table className="asset-table">
            <thead>
              <tr>
                <th>ASSET</th>
                <th>PRICE</th>
                <th>24H</th>
                <th>HELD</th>
                <th>ACTION</th>
              </tr>
            </thead>
            <tbody>
              {assets.map(asset=>{
                const held = parseFloat(holdings[asset.id]||0);
                const pct  = parseFloat(asset.base_price)
                  ? ((parseFloat(asset.current_price)-parseFloat(asset.base_price))/parseFloat(asset.base_price))*100
                  : 0;
                const up = pct>=0;
                return(
                  <tr key={asset.id}
                    className={selAsset?.id===asset.id?"active-row":""}
                    onClick={()=>openPanel(asset, side)}>
                    <td>
                      <div className="at-asset-wrap">
                        <span className="at-icon">{ICONS[asset.category_name]||"◆"}</span>
                        <div>
                          <div className="at-name">{(asset.category_name||"ASSET").toUpperCase()}</div>
                          <div className="at-sub">{asset.name}</div>
                        </div>
                      </div>
                    </td>
                    <td><span className="at-price">◆{parseFloat(asset.current_price).toFixed(2)}</span></td>
                    <td>
                      <span className={up?"at-chg-up":"at-chg-down"}>
                        {up?"▲":"▼"} {Math.abs(pct).toFixed(1)}%
                      </span>
                    </td>
                    <td><span className="at-held">{held>0?held:0}</span></td>
                    <td>
                      <div className="at-actions" onClick={e=>e.stopPropagation()}>
                        <button className="at-btn-buy" onMouseEnter={()=>soundFX.blip()} onClick={()=>openPanel(asset,"buy")}>BUY</button>
                        <button className="at-btn-sell" onMouseEnter={()=>soundFX.blip()} onClick={()=>openPanel(asset,"sell")}>SELL</button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* RIGHT: trade panel */}
        <div className="exchange-right">
          {!selAsset ? (
            <div className="trade-panel-empty">
              SELECT AN ASSET TO TRADE
            </div>
          ) : (
            <div className="trade-panel panel-border">
              {/* Panel header */}
              <div className="tp-header">
                <div>
                  <div className="tp-label">TRADING</div>
                  <div className="tp-name">{(selAsset.category_name||"ASSET").toUpperCase()}</div>
                  <div className="tp-sub">{selAsset.name}</div>
                </div>
                <div className="tp-icon">{ICONS[selAsset.category_name]||"◆"}</div>
              </div>

              <div className="tp-body">
                {/* Last price & Chart */}
                <div className="tp-price-block">
                  <div className="tp-price-label">LAST PRICE</div>
                  <div className="tp-price-val">◆ {parseFloat(selAsset.current_price).toFixed(2)}</div>
                  <div className="tp-chart-wrap" style={{ height: 120, marginTop: 16, borderBottom: "1px solid var(--border)", paddingBottom: 16 }}>
                    {history.length > 1 ? (
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={history}>
                          <YAxis domain={['dataMin', 'dataMax']} hide />
                          <Line type="stepAfter" dataKey="price" stroke="var(--cyan)" strokeWidth={2} dot={false} isAnimationActive={false} />
                        </LineChart>
                      </ResponsiveContainer>
                    ) : (
                      <div style={{ height: "100%", display: "flex", alignItems: "center", justifyContent: "center", color: "var(--border)", fontFamily: "var(--font-pixel)", fontSize: 10 }}>AWAITING TICK DATA...</div>
                    )}
                  </div>
                </div>

                {/* Buy / Sell toggle */}
                <div>
                  <div className="tp-price-label" style={{marginBottom:8}}>SIDE</div>
                  <div className="tp-side-toggle">
                    <button className={`tp-side-btn ${side==="buy"?"buy-active":""}`} onMouseEnter={()=>soundFX.blip()} onClick={()=>setSide("buy")}>► BUY</button>
                    <button className={`tp-side-btn ${side==="sell"?"sell-active":""}`} onMouseEnter={()=>soundFX.blip()} onClick={()=>setSide("sell")}>▼ SELL</button>
                  </div>
                </div>

                {/* Quantity */}
                <div>
                  <div className="qty-label">QUANTITY</div>
                  <div className="qty-stepper">
                    <button className="qty-dec" onClick={()=>changeQty(-1)}>−</button>
                    <input
                      type="number" min="0.1" step="0.1"
                      className="qty-input"
                      value={qty}
                      onChange={e=>setQty(Math.max(0.1, parseFloat(e.target.value)||0))}
                    />
                    <button className="qty-inc" onClick={()=>changeQty(1)}>+</button>
                  </div>
                </div>

                {/* Total */}
                <div className="tp-total-row">
                  <span className="tp-total-label">TOTAL</span>
                  <span className="tp-total-val">◆ {cost.toFixed(2)}</span>
                </div>

                {/* Messages */}
                {tradeMsg && <div className="tp-msg-ok">✔ {tradeMsg}</div>}
                {tradeErr && <div className="tp-msg-err">▶ {tradeErr}</div>}

                {/* Execute */}
                <button
                  className={`tp-exec-btn ${side}`}
                  onClick={executeTrade}
                  disabled={executing}
                >
                  {executing ? "PROCESSING..." : side==="buy" ? "► EXECUTE BUY" : "▼ EXECUTE SELL"}
                </button>

                {/* Circuit breaker warning */}
                {selAsset.circuit_breaker_tripped && (
                  <div style={{
                    border:"1px solid var(--red)", color:"var(--red)",
                    padding:"8px 12px", fontFamily:"var(--font-pixel)",
                    fontSize:8, letterSpacing:2, animation:"blink 1s step-end infinite"
                  }}>
                    ⚠ CIRCUIT BREAKER TRIPPED — TRADING HALTED
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
        </div>
      </div>
    </div>
  );
}
