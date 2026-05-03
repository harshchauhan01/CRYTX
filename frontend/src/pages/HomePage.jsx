import { useState, useEffect, useRef } from "react";
import { Link } from "react-router-dom";
import axios from "axios";
import "./HomePage.css";

const API_BASE = "http://127.0.0.1:8001/api/market";

const CATEGORY_ICONS = { Food:"🌾", Air:"💨", Medical:"💊", Energy:"⚡", Water:"💧", Ammo:"🎯", default:"◆" };

function fmtVal(v) {
  const n = parseFloat(v)||0;
  if(n>=1_000_000) return (n/1_000_000).toFixed(2)+"M";
  if(n>=1_000)     return (n/1_000).toFixed(1)+"K";
  return n.toFixed(0);
}

function buildBars(current, base, count=22) {
  const bars=[]; let p=parseFloat(base)||parseFloat(current)||100;
  for(let i=0;i<count;i++){p*=(1+(Math.random()-0.49)*0.04); bars.push(Math.max(p,1));}
  bars[count-1]=parseFloat(current)||p;
  const mx=Math.max(...bars);
  return bars.map(b=>Math.round((b/mx)*100));
}

function MiniChart({current,base,isUp}){
  const bars=useRef(buildBars(current,base, 15));
  return(
    <div className="hm-chart">
      {bars.current.map((h,i)=>(
        <div key={i} className="hm-bar" style={{
          height:`${Math.max(h, 10)}%`,
          background: isUp ? 'var(--green)' : 'var(--red)',
          opacity: 0.5 + (h/100)*0.5
        }}/>
      ))}
    </div>
  );
}

function Ticker({assets}){
  if(!assets.length) return null;
  const doubled=[...assets,...assets];
  return(
    <div className="home-ticker-wrap">
      <div className="home-ticker-track">
        {doubled.map((a,i)=>{
          const pct=parseFloat(a.base_price)
            ?((parseFloat(a.current_price)-parseFloat(a.base_price))/parseFloat(a.base_price))*100
            :0;
          const up=pct>=0;
          const sym=a.name.substring(0,4).toUpperCase();
          return(
            <span key={i} className="htick-item">
              {CATEGORY_ICONS[a.category_name]||"◆"}
              <span className="htick-name">{sym}</span>
              <span className="htick-price">◆ {parseFloat(a.current_price).toFixed(2)}</span>
              <span className={up?"htick-up":"htick-down"}>{up?"▲":"▼"} {Math.abs(pct).toFixed(1)}%</span>
              <span className="htick-sep">|</span>
            </span>
          );
        })}
      </div>
    </div>
  );
}

export default function HomePage({ isAuthenticated }) {
  const [assets, setAssets]         = useState([]);
  const [leaders, setLeaders]       = useState([]);
  const [totalTraders]              = useState(42891);
  const [blockNum]                  = useState(()=>"#"+Math.floor(Date.now()/10000).toString(16).toUpperCase().slice(-7));

  useEffect(() => {
    axios.get(`${API_BASE}/assets/`).then(r => setAssets(r.data.results||r.data)).catch(()=>{});
    const token = localStorage.getItem("access_token");
    if(token) {
      axios.get(`${API_BASE}/users-by-networth/`,{headers:{Authorization:`Bearer ${token}`}})
        .then(r=>setLeaders((r.data||[]).slice(0,5))).catch(()=>{});
    }
  }, []);

  const totalVol = assets.reduce((s,a)=>s+parseFloat(a.buy_volume||0)+parseFloat(a.sell_volume||0),0);

  return (
    <div>
      {/* ── Public Navbar ── */}
      {!isAuthenticated && (
        <nav className="pub-nav">
          <div className="pub-nav-inner">
            <Link to="/" className="pub-logo">
              <span className="crystal-logo"/>
              <span className="pub-logo-text">CRYTX</span>
            </Link>
            <div className="pub-links">
              <a href="#market"    className="pub-link">MARKET</a>
              <a href="#how"       className="pub-link">SYSTEM</a>
              <a href="#leaders"   className="pub-link">LEADERS</a>
              <Link to="/login" className="pub-link">ENTER</Link>
            </div>
            <Link to="/login" className="pub-nav-cta">
              JACK IN
            </Link>
          </div>
        </nav>
      )}

      {/* ── HERO ── */}
      <div style={{maxWidth:1440, margin:"0 auto", padding:"0 80px"}}>
        <div className="hero" style={{padding:"80px 0", minHeight:"auto"}}>
          <div className="hero-left">
            <div className="hero-badge">LIVE · YEAR 2147</div>
            <h1 className="hero-title">
              <span className="t1">CRYSTAL</span>
              <span className="t2">EXCHANGE_</span>
            </h1>
            <p className="hero-sub">
              The old money is ash. Trade crystals for the things that keep you breathing — food, air, energy, medicine. Build a syndicate. Outlast the market. Rule what's left.
            </p>
            <div className="hero-btns">
              <Link to={isAuthenticated?"/market":"/login"} className="px-btn px-btn-cyan" style={{fontSize:9,letterSpacing:2}}>
                ► START TRADING
              </Link>
              <a href="#leaders" className="px-btn px-btn-green" style={{fontSize:9,letterSpacing:2}}>
                VIEW LEADERS
              </a>
            </div>
          </div>
          <div className="hero-right">
            <div className="crystal-3d-scene">
              <div className="crystal-3d-glow" />
              <div className="crystal-3d">
                <div className="c-face c-front"></div>
                <div className="c-face c-back"></div>
                <div className="c-face c-right"></div>
                <div className="c-face c-left"></div>
                <div className="c-face c-top"></div>
                <div className="c-face c-bottom"></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── Hero Stats Bar ── */}
      <div className="hero-stats">
        <div className="hero-stats-inner">
          <div><div className="hstat-label">BLOCK</div><div className="hstat-val">{blockNum}</div></div>
          <div><div className="hstat-label">TRADERS</div><div className="hstat-val">{totalTraders.toLocaleString()}</div></div>
          <div><div className="hstat-label">VOLUME</div><div className="hstat-val">◆ {fmtVal(totalVol)}</div></div>
          <div><div className="hstat-label">ASSETS</div><div className="hstat-val">{assets.length}</div></div>
        </div>
      </div>

      {/* ── Ticker ── */}
      <Ticker assets={assets}/>

      {/* ── Live Market Cards ── */}
      <div className="home-section" id="market">
        <div className="section-label">MKT / 01</div>
        <h2 className="page-title">LIVE WASTELAND MARKET</h2>
        <div className="home-market-grid">
          {assets.map(asset=>{
            const pct=parseFloat(asset.base_price)
              ?((parseFloat(asset.current_price)-parseFloat(asset.base_price))/parseFloat(asset.base_price))*100
              :0;
            const isUp=pct>=0;
            return(
              <div key={asset.id} className="hm-card">
                <div className="hm-card-head">
                  <div>
                    <div className="hm-cat">{(asset.category_name||"ASSET").toUpperCase()}</div>
                    <div className="hm-name">{asset.name}</div>
                  </div>
                  <div className="hm-icon">{CATEGORY_ICONS[asset.category_name]||"◆"}</div>
                </div>
                <div className="hm-price-label">PRICE</div>
                <div className="hm-price-row">
                  <div className="hm-price"><span className="psym">◆</span>{parseFloat(asset.current_price).toFixed(2)}</div>
                  <span className={isUp?"hm-chg-up":"hm-chg-down"}>
                    {isUp?"▲":"▼"} {Math.abs(pct).toFixed(2)}%
                  </span>
                </div>
                <MiniChart current={asset.current_price} base={asset.base_price} isUp={isUp}/>
              </div>
            );
          })}
        </div>
        {assets.length===0 && <div className="px-info" style={{marginTop:16}}>▶ Market data loading...</div>}
      </div>

      {/* ── How It Works ── */}
      <div className="home-section" id="how" style={{paddingTop:0}}>
        <div className="section-label">SYS / 02</div>
        <h2 className="page-title">HOW IT WORKS</h2>
        <div className="how-grid">
          <div className="how-card">
            <div className="how-num">01</div>
            <div className="how-title">JACK IN</div>
            <p className="how-desc">Create your trader handle and claim your free starter wallet of 10,000 crystals. No real money, pure strategy.</p>
          </div>
          <div className="how-card">
            <div className="how-num">02</div>
            <div className="how-title">TRADE THE WASTELAND</div>
            <p className="how-desc">Buy and sell assets across categories — food, air, energy, medicine. Prices move in real-time driven by supply, demand, and chaos events.</p>
          </div>
          <div className="how-card">
            <div className="how-num">03</div>
            <div className="how-title">OUTLAST THEM ALL</div>
            <p className="how-desc">The market rewards patience and ruthlessness. Build your net worth, climb the leaderboard, and become a Crystal Baron.</p>
          </div>
        </div>
      </div>

      {/* ── Leaderboard Strip ── */}
      <div className="home-section" id="leaders" style={{paddingTop:0}}>
        <div className="section-label">LDR / 03</div>
        <h2 className="page-title">TOP CRYSTAL BARONS</h2>
        {leaders.length>0 ? (
          <>
            <table className="home-lb-table">
              <thead><tr>
                <th>RANK</th><th>TRADER</th><th>NET WORTH</th><th>Δ</th>
              </tr></thead>
              <tbody>
                {leaders.map((p,i)=>{
                  const rank=p.rank||i+1;
                  const up=Math.random()>0.4;
                  return(
                    <tr key={i}>
                      <td><span className={`hlb-rank${rank===1?" r1":rank===2?" r2":rank===3?" r3":""}`}>#{String(rank).padStart(2,"0")}</span></td>
                      <td><span className="hlb-av"/><span className="hlb-name">{(p.username||"ANON").toUpperCase()}</span></td>
                      <td><span className="hlb-nw">◆ {fmtVal(p.net_worth||0)}</span></td>
                      <td><span className={up?"hlb-up":"hlb-dn"}>{up?"▲":"▼"}</span></td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
            <div className="home-lb-stats">
              <div className="hlb-stat"><div className="hlb-stat-label">TOTAL VOL 24H</div><div className="hlb-stat-val g">◆ {fmtVal(leaders.reduce((s,r)=>s+(r.net_worth||0),0))}</div></div>
              <div className="hlb-stat"><div className="hlb-stat-label">ACTIVE CARDS</div><div className="hlb-stat-val c">{assets.length * 12}</div></div>
              <div className="hlb-stat"><div className="hlb-stat-label">COMPANIES</div><div className="hlb-stat-val o">2,317</div></div>
              <div className="hlb-stat"><div className="hlb-stat-label">SURVIVORS</div><div className="hlb-stat-val w">{totalTraders.toLocaleString()}</div></div>
            </div>
          </>
        ) : (
          <div className="px-info">▶ Login to view the leaderboard rankings.</div>
        )}
      </div>

      {/* ── CTA Banner ── */}
      <div className="home-cta-band">
        <div className="home-cta-inner">
          <div>
            <div className="home-cta-title">READY TO ENTER THE EXCHANGE?</div>
            <div className="home-cta-sub">◆ FREE STARTER WALLET · 10,000 · CRYSTALS ON ENTRY</div>
          </div>
          <Link to={isAuthenticated?"/market":"/signup"} className="px-btn px-btn-cyan" style={{fontSize:10,letterSpacing:2,padding:"14px 28px"}}>
            ► {isAuthenticated?"OPEN EXCHANGE FLOOR":"CLAIM YOUR HANDLE"}
          </Link>
        </div>
      </div>

      {/* ── Footer ── */}
      <div style={{borderTop:"1px solid var(--border)"}}>
        <div className="home-footer">
          <div className="home-footer-logo">◆ CRYTX</div>
          <div className="home-footer-note">CRYSTAL EXCHANGE · YEAR 2147 · ALL RIGHTS BURNED</div>
        </div>
      </div>
    </div>
  );
}
