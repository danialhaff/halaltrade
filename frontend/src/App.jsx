import React, { useState, useEffect, useRef, useCallback } from 'react';
import { 
  Crosshair, ShieldCheck, Zap, BarChart2, Activity, Target, AlertTriangle, FileText, Home, TrendingUp, Globe, RefreshCw
} from 'lucide-react';
import axios from 'axios';
import logoImg from './logo.png';
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer,
  AreaChart, Area, ReferenceLine
} from 'recharts';
import { createChart, CandlestickSeries, HistogramSeries } from 'lightweight-charts';
import './index.css';

const API = 'http://localhost:8000';

// ─── Helper Components ──────────────────────────────────────

function Badge({ signal }) {
  const map = {
    'STRONG BUY': 'badge-strongbuy',
    'BUY': 'badge-buy',
    'HOLD': 'badge-hold',
    'SELL': 'badge-sell',
    'STRONG SELL': 'badge-sell',
    'HARAM': 'badge-haram',
    'ERROR': 'badge-haram',
  };
  return <span className={`badge ${map[signal] || 'badge-haram'}`}>{signal}</span>;
}

function StatCard({ label, value, color }) {
  return (
    <div className="stat-card">
      <div className="label">{label}</div>
      <div className="val-md" style={{ color: color || 'white', marginTop: 4 }}>{value}</div>
    </div>
  );
}

function ProgressBar({ value, max, color }) {
  const pct = Math.min(100, (value / max) * 100);
  return (
    <div className="progress-track">
      <div className="progress-fill" style={{ width: `${pct}%`, background: color || 'var(--green)' }} />
    </div>
  );
}

function Skeleton({ h = 16, w = '100%' }) {
  return <div className="skeleton" style={{ height: h, width: w, marginBottom: 8 }} />;
}

// ─── Home Dashboard Tab ──────────────────────────────────────

function HomeTab() {
  const [data, setData] = useState(null);
  const [ipos, setIpos] = useState([]);
  const [earnings, setEarnings] = useState([]);
  const [watchlist, setWatchlist] = useState([]);
  const [loading, setLoading] = useState(true);

  const [watchlistLoading, setWatchlistLoading] = useState(true);

  useEffect(() => {
    // Fetch fast dashboard components
    const fetchDashboard = async () => {
      try {
        const [dashRes, ipoRes, earnRes] = await Promise.all([
          axios.get(`${API}/api/market/dashboard`),
          axios.get(`${API}/api/market/ipos`),
          axios.get(`${API}/api/earnings`)
        ]);
        setData(dashRes.data);
        setIpos(ipoRes.data.ipos || []);
        setEarnings(earnRes.data.earnings || []);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };

    // Fetch slow watchlist component separately
    const fetchWatchlist = async () => {
      try {
        const watchRes = await axios.get(`${API}/api/watchlist`);
        setWatchlist(watchRes.data.watchlist || []);
      } catch (e) {
        console.error(e);
      } finally {
        setWatchlistLoading(false);
      }
    };

    fetchDashboard();
    fetchWatchlist();
  }, []);

  if (loading) return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div className="panel fade-up"><Skeleton h={150} /></div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        <div className="panel fade-up"><Skeleton h={300} /></div>
        <div className="panel fade-up"><Skeleton h={300} /></div>
      </div>
    </div>
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* VIX & Macro Row */}
      <div style={{ display: 'grid', gridTemplateColumns: '300px 1fr', gap: 16 }}>
        {/* VIX Fear Gauge */}
        <div className={`panel fade-up ${data?.vix?.value > 25 ? 'accent-red' : data?.vix?.value > 15 ? 'accent-amber' : 'accent-green'}`} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '24px 16px' }}>
          <div className="section-title" style={{ width: '100%', textAlign: 'left', marginBottom: 16 }}><AlertTriangle size={14} /> Volatility Index (VIX)</div>
          <div className="val-lg" style={{ fontSize: '3rem', color: data?.vix?.value > 25 ? 'var(--red)' : data?.vix?.value > 15 ? 'var(--amber)' : 'var(--green)' }}>
            {data?.vix?.value}
          </div>
          <div style={{ fontSize: '1.2rem', fontWeight: 600, marginTop: 8, color: 'white' }}>{data?.vix?.status}</div>
          <div style={{ fontFamily: 'var(--mono)', fontSize: '0.85rem', color: data?.vix?.change_pct >= 0 ? 'var(--red)' : 'var(--green)', marginTop: 4 }}>
            {data?.vix?.change_pct >= 0 ? '+' : ''}{data?.vix?.change_pct}% Today
          </div>
        </div>

        {/* Top AI Picks */}
        <div className="panel fade-up">
          <div className="section-title"><Target size={14} /> My Halal Trade AI Picks</div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, marginTop: 12 }}>
            {data?.top_picks?.map(pick => (
              <div key={pick.ticker} style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border)', borderRadius: 8, padding: 16, position: 'relative', overflow: 'hidden' }}>
                <div style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: 3, background: 'var(--green)' }} />
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                  <span style={{ fontSize: '1.4rem', fontWeight: 800, fontFamily: 'var(--mono)' }}>{pick.ticker}</span>
                  <span style={{ background: 'rgba(0,255,170,0.1)', color: 'var(--green)', padding: '2px 6px', borderRadius: 4, fontSize: '0.7rem', fontWeight: 700 }}>{pick.signal}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6, fontSize: '0.8rem' }}>
                  <span className="label">Conviction</span>
                  <span style={{ color: 'var(--green)', fontWeight: 700 }}>{pick.conviction}%</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6, fontSize: '0.8rem' }}>
                  <span className="label">Target Profit</span>
                  <span style={{ color: 'white', fontFamily: 'var(--mono)' }}>+{pick.target_profit_pct}%</span>
                </div>
              </div>
            ))}
            {(!data?.top_picks || data.top_picks.length === 0) && (
              <div style={{ color: 'var(--muted)', fontSize: '0.85rem', gridColumn: 'span 3', textAlign: 'center', padding: '20px' }}>No Strong Buy signals currently available.</div>
            )}
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        {/* Upcoming IPOs */}
        <div className="panel fade-up accent-blue">
          <div className="section-title"><TrendingUp size={14} /> Global Upcoming IPOs</div>
          <div className="table-responsive"><table className="data-table" style={{ marginTop: 8 }}>
            <thead>
              <tr>
                <th>Company</th>
                <th>Ticker</th>
                <th>Sector</th>
                <th style={{ textAlign: 'right' }}>Est. Valuation</th>
                <th style={{ textAlign: 'right' }}>Expected</th>
              </tr>
            </thead>
            <tbody>
              {ipos.map((ipo, i) => (
                <tr key={i}>
                  <td style={{ fontWeight: 600, color: 'white' }}>{ipo.company}</td>
                  <td style={{ fontFamily: 'var(--mono)', color: 'var(--blue)' }}>{ipo.symbol}</td>
                  <td style={{ fontSize: '0.8rem', color: 'var(--muted)' }}>{ipo.sector}</td>
                  <td style={{ textAlign: 'right', fontFamily: 'var(--mono)' }}>{ipo.est_valuation}</td>
                  <td style={{ textAlign: 'right', fontSize: '0.8rem' }}>{ipo.expected_date}</td>
                </tr>
              ))}
            </tbody>
          </table></div>
        </div>

        {/* Earnings Calendar */}
        <div className="panel fade-up accent-amber">
          <div className="section-title"><Target size={14} /> Upcoming Earnings (Watchlist)</div>
          {earnings.length === 0 ? <div style={{ color: 'var(--muted)', fontSize: '0.85rem' }}>No upcoming earnings found.</div> : (
            <div className="table-responsive"><table className="data-table" style={{ marginTop: 8 }}>
              <thead><tr><th>Ticker</th><th>Price</th><th style={{ textAlign: 'right' }}>Earnings Date</th></tr></thead>
              <tbody>
                {earnings.slice(0, 5).map((e, i) => (
                  <tr key={i}>
                    <td style={{ fontWeight: 600, color: 'white' }}>{e.ticker}</td>
                    <td style={{ fontFamily: 'var(--mono)' }}>${e.price.toFixed(2)}</td>
                    <td style={{ textAlign: 'right', color: 'var(--amber)' }}>{e.next_earnings}</td>
                  </tr>
                ))}
              </tbody>
            </table></div>
          )}
        </div>

        {/* Global Market News */}
        <div className="panel fade-up">
          <div className="section-title"><Globe size={14} /> Global Macro News</div>
          <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 8, margin: 0, padding: 0, marginTop: 8 }}>
            {data?.market_news?.length > 0 ? data.market_news.map((h, i) => (
              <li key={i} style={{ padding: '12px 14px', borderLeft: '3px solid var(--purple)', background: 'rgba(168, 85, 247, 0.05)', fontSize: '0.85rem', lineHeight: 1.4, borderRadius: '0 4px 4px 0' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px', fontSize: '0.75rem', color: 'var(--muted)', fontFamily: 'var(--mono)' }}>
                  <span>{typeof h === 'string' ? 'Macro' : h.publisher}</span>
                  <span>{typeof h === 'string' ? '' : h.time}</span>
                </div>
                <a href={typeof h === 'string' ? '#' : h.link} target="_blank" rel="noopener noreferrer" style={{ color: 'white', textDecoration: 'none', fontWeight: 500 }}>
                  {typeof h === 'string' ? h : h.title}
                </a>
                {typeof h !== 'string' && h.effect && (
                  <div style={{ marginTop: '6px', fontSize: '0.75rem', color: h.effect.includes('Bullish') ? 'var(--green)' : h.effect.includes('Bearish') || h.effect.includes('Negative') || h.effect.includes('High volatility') ? 'var(--red)' : 'var(--blue)' }}>
                    <span style={{ fontWeight: 600 }}>AI Remark: </span>
                    {h.effect}
                  </div>
                )}
              </li>
            )) : <li style={{ color: 'var(--muted)', fontSize: '0.8rem' }}>No recent macro news found.</li>}
          </ul>
        </div>
      </div>

      {/* Global Watchlist Overview */}
      <div className="panel fade-up" style={{ marginTop: '8px' }}>
        <div className="section-title"><Activity size={14} /> Global Market Screener (Shariah-Compliant)</div>
        <div style={{ maxHeight: '400px', overflowY: 'auto', paddingRight: '4px' }}>
          <div className="table-responsive"><table className="data-table">
            <thead style={{ position: 'sticky', top: 0, background: 'var(--bg-card)', zIndex: 10 }}>
              <tr>
                <th>Symbol</th>
                <th>Price</th>
                <th>Change</th>
                <th>Volume</th>
                <th>Market Cap</th>
                <th>52W High</th>
                <th>52W Low</th>
              </tr>
            </thead>
            <tbody>
              {watchlistLoading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <tr key={`skel-${i}`}>
                    <td colSpan={7}><Skeleton h={24} /></td>
                  </tr>
                ))
              ) : (
                watchlist.map(item => (
                  <tr key={item.ticker}>
                    <td style={{ fontWeight: 600, color: 'white' }}>{item.ticker}</td>
                    <td>${item.price?.toFixed(2) || '—'}</td>
                    <td style={{ color: item.change_pct >= 0 ? 'var(--green)' : 'var(--red)', fontWeight: 600 }}>
                      {item.change_pct >= 0 ? '+' : ''}{item.change_pct?.toFixed(2)}%
                    </td>
                    <td>{item.volume?.toLocaleString() || '—'}</td>
                    <td>{item.market_cap ? `$${(item.market_cap / 1e9).toFixed(2)}B` : '—'}</td>
                    <td>${item.week52_high?.toFixed(2) || '—'}</td>
                    <td>${item.week52_low?.toFixed(2) || '—'}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table></div>
        </div>
      </div>
    </div>
  );
}

// ─── TradingView Chart Component ─────────────────────────────

function TradingChart({ ticker }) {
  const chartContainerRef = useRef();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [period, setPeriod] = useState('6mo');

  useEffect(() => {
    if (!ticker) return;
    
    let chart;
    const fetchAndRender = async () => {
      setLoading(true); setError(null);
      try {
        const res = await axios.get(`${API}/api/chart/${ticker}?period=${period}`);
        if (res.data.error) {
          setError(res.data.error);
          return;
        }
        
        const data = res.data.data;
        if (!chartContainerRef.current || !data) return;
        
        chartContainerRef.current.innerHTML = '';
        
        chart = createChart(chartContainerRef.current, {
          layout: { background: { type: 'solid', color: 'transparent' }, textColor: '#8b96a8' },
          grid: { vertLines: { color: 'rgba(255,255,255,0.05)' }, horzLines: { color: 'rgba(255,255,255,0.05)' } },
          crosshair: { mode: 1 },
          rightPriceScale: { borderColor: 'rgba(255,255,255,0.1)' },
          timeScale: { borderColor: 'rgba(255,255,255,0.1)' },
          autoSize: true,
        });

        const candlestickSeries = chart.addSeries(CandlestickSeries, {
          upColor: '#00ffaa', downColor: '#ff4d4d', borderVisible: false,
          wickUpColor: '#00ffaa', wickDownColor: '#ff4d4d',
        });
        candlestickSeries.setData(data);

        const volumeSeries = chart.addSeries(HistogramSeries, {
          color: 'rgba(255, 255, 255, 0.1)', priceFormat: { type: 'volume' },
          priceScaleId: '', scaleMargins: { top: 0.8, bottom: 0 }
        });
        
        const volData = data.map(d => ({
          time: d.time,
          value: d.value,
          color: d.close >= d.open ? 'rgba(0, 255, 170, 0.2)' : 'rgba(255, 77, 77, 0.2)'
        }));
        volumeSeries.setData(volData);
        chart.timeScale().fitContent();
        
      } catch (err) {
        console.error("Chart Error:", err);
        setError(`Failed to load chart data: ${err.message || String(err)}`);
      } finally {
        setLoading(false);
      }
    };
    
    fetchAndRender();
    return () => { if (chart) chart.remove(); };
  }, [ticker, period]);

  const timeframes = [
    { label: '1W', val: '1wk' },
    { label: '1M', val: '1mo' },
    { label: '3M', val: '3mo' },
    { label: '6M', val: '6mo' },
    { label: 'YTD', val: 'ytd' },
    { label: '1Y', val: '1y' },
    { label: '2Y', val: '2y' },
    { label: '5Y', val: '5y' }
  ];

  return (
    <div className="panel fade-up" style={{ padding: '4px', height: '400px', display: 'flex', flexDirection: 'column' }}>
      <div style={{ padding: '12px 16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span className="section-title" style={{ margin: 0 }}><Activity size={14} /> Interactive Chart — {ticker}</span>
        <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
          {loading && <span style={{ color: 'var(--amber)', fontSize: '0.8rem', marginRight: '10px' }}>Loading...</span>}
          {timeframes.map(t => (
            <button 
              key={t.val} 
              onClick={() => setPeriod(t.val)}
              style={{
                background: period === t.val ? 'var(--blue)' : 'rgba(255,255,255,0.1)',
                border: 'none', color: 'white', padding: '4px 8px', borderRadius: '4px',
                fontSize: '0.75rem', cursor: 'pointer', fontFamily: 'var(--mono)', transition: 'background 0.2s'
              }}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>
      {error && <div style={{ padding: '20px', color: 'var(--red)', textAlign: 'center' }}>{error}</div>}
      <div ref={chartContainerRef} style={{ flex: 1, position: 'relative' }} />
    </div>
  );
}

// ─── Tabs ────────────────────────────────────────────────────

function TerminalTab({ portfolio }) {
  const [ticker, setTicker] = useState('AAPL');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const analyze = async () => {
    if (!ticker.trim()) return;
    setLoading(true); setError(null); setData(null);
    try {
      const res = await axios.get(`${API}/api/analyze/${ticker.trim()}`);
      if (res.data.error) setError(res.data.error);
      else setData(res.data);
    } catch { setError('Cannot connect to AI Engine. Is the backend running?'); }
    setLoading(false);
  };

  const handleKey = e => { if (e.key === 'Enter') analyze(); };
  const ai = data?.ai_signal;
  const sh = data?.shariah;
  const rm = data?.risk_model;
  const mc = data?.monte_carlo;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* Search Bar */}
      <div className="panel" style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
        <Crosshair size={16} color="var(--green)" />
        <input id="ticker-input" className="input" style={{ flex: 1 }} value={ticker}
          onChange={e => setTicker(e.target.value.toUpperCase())} onKeyDown={handleKey}
          placeholder="Enter ticker symbol (e.g. AAPL, NVDA, TSLA)" />
        <button id="analyze-btn" className="btn" onClick={analyze} disabled={loading}>
          {loading ? '⏳ ANALYZING...' : '⚡ ANALYZE'}
        </button>
      </div>

      {error && <div className="panel accent-red fade-up" style={{ color: 'var(--red)', fontFamily: 'var(--mono)', fontSize: '0.85rem' }}>⚠ {error}</div>}

      {loading && (
        <div className="panel fade-up" style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: 16 }}>
          <div><Skeleton h={200} /><Skeleton h={24} /><Skeleton h={24} /></div>
          <div><Skeleton h={60} /><Skeleton h={60} /><Skeleton h={60} /></div>
        </div>
      )}

      {data && !loading && (
        <>
          {/* Shariah Status Banner */}
          <div className={`panel fade-up ${sh?.is_compliant ? 'accent-green' : 'accent-red'}`}
            style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '12px 20px' }}>
            <ShieldCheck size={18} color={sh?.is_compliant ? 'var(--green)' : 'var(--red)'} />
            <span style={{ fontFamily: 'var(--mono)', fontSize: '0.8rem', fontWeight: 600, color: sh?.is_compliant ? 'var(--green)' : 'var(--red)' }}>
              {data.ticker} — {sh?.is_compliant ? 'SHARIAH COMPLIANT (HALAL)' : 'NON-COMPLIANT (HARAM) — Trade Blocked'}
            </span>
          </div>

          {/* Main Chart */}
          <TradingChart ticker={data.ticker} />

          {/* Main Analysis Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: '200px 1fr', gap: 16 }}>
            {/* Conviction Gauge */}
            <div className="panel fade-up" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 8 }}>
              <div className="label">Conviction Score</div>
              <div className="gauge-wrap">
                <div className="gauge-ring" style={{ borderColor: 'rgba(255,255,255,0.07)', borderBottomColor: 'transparent', borderLeftColor: 'transparent', transform: 'rotate(-45deg)' }} />
                <div className="gauge-ring" style={{
                  borderColor: ai?.conviction > 75 ? 'var(--green)' : ai?.conviction > 50 ? 'var(--amber)' : 'var(--red)',
                  borderBottomColor: 'transparent', borderLeftColor: 'transparent',
                  transform: `rotate(${-45 + (ai?.conviction / 100) * 180}deg)`,
                  boxShadow: ai?.conviction > 60 ? `0 0 12px var(--green-glow)` : 'none'
                }} />
              </div>
              <div className="val-lg" style={{ color: ai?.conviction > 75 ? 'var(--green)' : ai?.conviction > 50 ? 'var(--amber)' : 'var(--red)', fontSize: '2.2rem' }}>
                {ai?.conviction}<span style={{ fontSize: '1rem' }}>%</span>
              </div>
              <Badge signal={ai?.signal} />
            </div>

            {/* Factor Breakdown */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {[
                { label: 'Technical Analysis (RSI/MACD/BB)', score: ai?.technical_score, reason: ai?.technical_reason, color: 'var(--green)' },
                { label: 'Fundamental Strength', score: ai?.fundamental_score, reason: ai?.fundamental_reason, color: 'var(--blue)' },
                { label: 'NLP News Sentiment', score: ai?.sentiment_score, reason: ai?.sentiment_reason, color: 'var(--amber)' },
              ].map(f => (
                <div key={f.label} className="panel fade-up" style={{ borderLeft: `3px solid ${f.color}`, padding: '14px 16px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                    <span style={{ fontSize: '0.8rem', fontWeight: 600 }}>{f.label}</span>
                    <span style={{ fontFamily: 'var(--mono)', fontSize: '0.9rem', color: f.color, fontWeight: 700 }}>{f.score}%</span>
                  </div>
                  <ProgressBar value={f.score} max={100} color={f.color} />
                  <p style={{ marginTop: 8, fontSize: '0.78rem', color: 'var(--muted)' }}>{f.reason}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Trade Setups Row */}
          {ai?.trade_setups && (
            <div className="panel fade-up" style={{ padding: '16px' }}>
              <div className="section-title" style={{ marginBottom: '12px' }}>
                <Target size={14} /> Recommended Trading Setups (Long Only)
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16 }}>
                {Object.entries(ai.trade_setups).map(([style, setup]) => (
                  <div key={style} style={{ background: 'rgba(0,0,0,0.2)', padding: '12px', borderRadius: '6px', border: '1px solid var(--border)' }}>
                    <div style={{ textTransform: 'uppercase', fontSize: '0.85rem', fontWeight: 'bold', color: 'var(--blue)', marginBottom: '8px' }}>
                      {style}
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                      <span className="label">Entry Point</span>
                      <span style={{ fontFamily: 'var(--mono)', fontSize: '0.9rem', color: 'white' }}>${setup.entry.toFixed(2)}</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                      <span className="label">Take Profit</span>
                      <div style={{ textAlign: 'right' }}>
                        <span style={{ fontFamily: 'var(--mono)', fontSize: '0.9rem', color: 'var(--green)' }}>${setup.tp.toFixed(2)}</span>
                        <span style={{ fontFamily: 'var(--mono)', fontSize: '0.7rem', color: 'var(--green)', marginLeft: '4px' }}>(+{setup.tp_pct}%)</span>
                      </div>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span className="label">Stop Loss</span>
                      <div style={{ textAlign: 'right' }}>
                        <span style={{ fontFamily: 'var(--mono)', fontSize: '0.9rem', color: 'var(--red)' }}>${setup.sl.toFixed(2)}</span>
                        <span style={{ fontFamily: 'var(--mono)', fontSize: '0.7rem', color: 'var(--red)', marginLeft: '4px' }}>(-{setup.sl_pct}%)</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TA Indicators Row */}
          {ai?.ta_data && (
            <div className="panel fade-up">
              <div className="section-title"><Activity size={12} /> Live Technical Indicators</div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 12 }}>
                <StatCard label="RSI (14)" value={ai.ta_data.rsi?.toFixed(1) || 'N/A'} color={ai.ta_data.rsi > 70 ? 'var(--red)' : ai.ta_data.rsi < 30 ? 'var(--green)' : 'var(--amber)'} />
                <StatCard label="MACD Hist" value={ai.ta_data.macd_hist?.toFixed(4) || 'N/A'} color={ai.ta_data.macd_hist > 0 ? 'var(--green)' : 'var(--red)'} />
                <StatCard label="MA Signal" value={ai.ta_data.golden_cross === true ? '🟢 Golden X' : ai.ta_data.golden_cross === false ? '🔴 Death X' : 'N/A'} color={ai.ta_data.golden_cross ? 'var(--green)' : 'var(--red)'} />
                <StatCard label="SMA 50" value={ai.ta_data.sma50 ? `$${ai.ta_data.sma50.toFixed(2)}` : 'N/A'} />
                <StatCard label="SMA 200" value={ai.ta_data.sma200 ? `$${ai.ta_data.sma200.toFixed(2)}` : 'N/A'} />
              </div>
            </div>
          )}

          {/* Monte Carlo Fan Chart */}
          {mc && !mc.error && (
            <div className="panel fade-up">
              <div className="section-title"><BarChart2 size={12} /> Monte Carlo Simulation ({mc.simulations} paths, 30 days)</div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 160px', gap: 16, alignItems: 'center' }}>
                <ResponsiveContainer width="100%" height={180}>
                  <AreaChart data={mc.fan_chart} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
                    <XAxis dataKey="day" tick={{ fontFamily: 'var(--mono)', fontSize: 10, fill: 'var(--muted)' }} />
                    <YAxis tick={{ fontFamily: 'var(--mono)', fontSize: 10, fill: 'var(--muted)' }} width={60} />
                    <Tooltip contentStyle={{ background: '#0d1421', border: '1px solid var(--border)', fontFamily: 'var(--mono)', fontSize: 11 }} />
                    <Area type="monotone" dataKey="p95" stroke="transparent" fill="rgba(0,255,170,0.05)" />
                    <Area type="monotone" dataKey="p75" stroke="transparent" fill="rgba(0,255,170,0.08)" />
                    <Area type="monotone" dataKey="p50" stroke="var(--green)" strokeWidth={2} fill="rgba(0,255,170,0.12)" dot={false} />
                    <Area type="monotone" dataKey="p25" stroke="transparent" fill="rgba(0,0,0,0.1)" />
                  </AreaChart>
                </ResponsiveContainer>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                  <StatCard label="Prob. Profit" value={`${mc.prob_profit}%`} color={mc.prob_profit > 50 ? 'var(--green)' : 'var(--red)'} />
                  <StatCard label="Expected Return" value={`${mc.expected_return_pct}%`} color={mc.expected_return_pct > 0 ? 'var(--green)' : 'var(--red)'} />
                  <StatCard label="Start Price" value={`$${mc.start_price}`} />
                </div>
              </div>
            </div>
          )}

          {/* Shariah Matrix */}
          <div className={`panel fade-up ${sh?.is_compliant ? 'accent-green' : 'accent-red'}`}>
            <div className="section-title"><ShieldCheck size={12} /> AAOIFI Shariah Financial Ratios</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              {[
                { label: 'Debt / Market Cap', val: sh?.debt_ratio, max: sh?.max_debt },
                { label: 'Cash / Market Cap', val: sh?.cash_ratio, max: sh?.max_cash },
                { label: 'Receivables / Market Cap', val: sh?.receivables_ratio, max: sh?.max_receivables },
              ].map(r => {
                const pct = r.val || 0;
                const over = pct > (r.max || 0.33);
                return (
                  <div key={r.label}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                      <span style={{ fontSize: '0.8rem' }}>{r.label}</span>
                      <span style={{ fontFamily: 'var(--mono)', fontSize: '0.8rem', color: over ? 'var(--red)' : 'var(--green)' }}>
                        {(pct * 100).toFixed(1)}% / {((r.max || 0) * 100).toFixed(0)}% max
                      </span>
                    </div>
                    <ProgressBar value={pct} max={r.max || 0.33} color={over ? 'var(--red)' : 'var(--green)'} />
                  </div>
                );
              })}
            </div>
          </div>

          {/* Smart Money Flow */}
          {ai?.smart_money && (
            <div className="panel fade-up">
              <div className="section-title"><Target size={12} /> Institutional & Smart Money Flow</div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16 }}>
                <StatCard label="Institutional Ownership" value={`${ai.smart_money.institutional_ownership?.toFixed(1)}%`} color={ai.smart_money.institutional_ownership > 50 ? 'var(--blue)' : 'white'} />
                <StatCard label="Short Ratio (Days to Cover)" value={ai.smart_money.short_ratio?.toFixed(2)} color={ai.smart_money.short_ratio > 5 ? 'var(--red)' : 'var(--green)'} />
                <StatCard label="Beta (Volatility vs Market)" value={ai.smart_money.beta?.toFixed(2)} color={ai.smart_money.beta > 1.2 ? 'var(--amber)' : 'white'} />
              </div>
            </div>
          )}

          {/* VaR + NLP News Row */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <div className="panel fade-up accent-blue">
              <div className="section-title"><AlertTriangle size={12} /> Value at Risk (95% Confidence)</div>
              {rm?.error ? (
                <p style={{ color: 'var(--red)', fontSize: '0.8rem' }}>Unavailable: {rm.error}</p>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                  <div><div className="label">Max 1-Day Loss ($1,000 position)</div>
                    <div className="val-lg" style={{ color: 'var(--red)', fontSize: '1.8rem' }}>-${rm?.var_dollar?.toFixed(2)}</div>
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                    <StatCard label="Confidence" value={`${rm?.confidence}%`} color="var(--blue)" />
                    <StatCard label="Daily σ (Sigma)" value={`${(rm?.sigma * 100).toFixed(2)}%`} />
                  </div>
                </div>
              )}
            </div>
            <div className="panel fade-up">
              <div className="section-title"><Zap size={12} /> Live NLP News — VADER Sentiment</div>
              <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 6, margin: 0, padding: 0 }}>
                {ai?.headlines?.length > 0 ? ai.headlines.map((h, i) => (
                  <li key={i} style={{ padding: '10px 12px', borderLeft: '3px solid var(--amber)', background: 'rgba(245,158,11,0.05)', fontSize: '0.8rem', lineHeight: 1.4 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px', fontSize: '0.7rem', color: 'var(--muted)', fontFamily: 'var(--mono)' }}>
                      <span>{typeof h === 'string' ? 'News' : h.publisher}</span>
                      <span>{typeof h === 'string' ? '' : h.time}</span>
                    </div>
                    <a href={typeof h === 'string' ? '#' : h.link} target="_blank" rel="noopener noreferrer" style={{ color: 'white', textDecoration: 'none' }}>
                      {typeof h === 'string' ? h : h.title}
                    </a>
                  </li>
                )) : <li style={{ color: 'var(--muted)', fontSize: '0.8rem' }}>No recent news found.</li>}
              </ul>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

function SignalsTab() {
  const [signals, setSignals] = useState([]);
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/api/signals`);
      setSignals(res.data.signals || []);
    } catch { }
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div className="panel" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 20px' }}>
        <div className="section-title" style={{ margin: 0 }}><Zap size={12} /> Live Signal Scanner — {signals.length} Assets Monitored</div>
        <button id="refresh-signals-btn" className="btn" onClick={load} disabled={loading}>
          <RefreshCw size={12} style={{ display: 'inline', marginRight: 6 }} />
          {loading ? 'SCANNING...' : 'REFRESH'}
        </button>
      </div>

      {loading && (
        <div className="panel">
          {[...Array(8)].map((_, i) => <Skeleton key={i} h={44} />)}
        </div>
      )}

      {!loading && signals.length > 0 && (
        <div className="panel fade-up" style={{ padding: 0 }}>
          <div className="table-responsive"><table className="data-table">
            <thead>
              <tr>
                <th>Ticker</th>
                <th>Signal</th>
                <th>Conviction</th>
                <th>Technical</th>
                <th>Fundamental</th>
                <th>Sentiment</th>
                <th>RSI</th>
                <th>MA Signal</th>
                <th>Intraday TP</th>
                <th>Intraday SL</th>
              </tr>
            </thead>
            <tbody>
              {signals.map(s => (
                <tr key={s.ticker}>
                  <td><span style={{ fontWeight: 700, color: 'white' }}>{s.ticker}</span></td>
                  <td><Badge signal={s.signal} /></td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <div style={{ width: 50, height: 5, background: 'rgba(255,255,255,0.06)', borderRadius: 3, overflow: 'hidden' }}>
                        <div style={{ height: '100%', width: `${s.conviction}%`, background: s.conviction > 75 ? 'var(--green)' : s.conviction > 50 ? 'var(--amber)' : 'var(--red)', borderRadius: 3 }} />
                      </div>
                      <span style={{ color: s.conviction > 75 ? 'var(--green)' : s.conviction > 50 ? 'var(--amber)' : 'var(--red)' }}>{s.conviction}%</span>
                    </div>
                  </td>
                  <td style={{ color: 'var(--green)' }}>{s.technical_score}%</td>
                  <td style={{ color: 'var(--blue)' }}>{s.fundamental_score}%</td>
                  <td style={{ color: 'var(--amber)' }}>{s.sentiment_score}%</td>
                  <td style={{ color: s.rsi > 70 ? 'var(--red)' : s.rsi < 30 ? 'var(--green)' : 'var(--muted)' }}>{s.rsi?.toFixed(1) || 'N/A'}</td>
                  <td>{s.golden_cross === true ? <span style={{ color: 'var(--green)' }}>Golden ✓</span> : s.golden_cross === false ? <span style={{ color: 'var(--red)' }}>Death ✗</span> : '—'}</td>
                  <td style={{ color: 'var(--green)' }}>${s.trade_setups?.intraday?.tp?.toFixed(2)}</td>
                  <td style={{ color: 'var(--red)' }}>${s.trade_setups?.intraday?.sl?.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table></div>
        </div>
      )}
    </div>
  );
}

function OptimizerTab() {
  const [tickers, setTickers] = useState('AAPL,NVDA,MSFT,TSLA');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const optimize = async () => {
    setLoading(true); setResult(null);
    try {
      const res = await axios.get(`${API}/api/optimize?tickers=${encodeURIComponent(tickers)}`);
      setResult(res.data);
    } catch { }
    setLoading(false);
  };

  const weights = result?.weights || {};
  const weightArr = Object.entries(weights).sort((a, b) => b[1] - a[1]);
  const colors = ['var(--green)', 'var(--blue)', 'var(--amber)', 'var(--purple)', 'var(--red)'];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div className="panel">
        <div className="section-title"><Target size={12} /> Markowitz Portfolio Optimizer (Risk-Parity)</div>
        <div style={{ display: 'flex', gap: 12, marginTop: 12 }}>
          <input id="optimizer-input" className="input" style={{ flex: 1 }} value={tickers}
            onChange={e => setTickers(e.target.value.toUpperCase())} placeholder="e.g. AAPL,NVDA,MSFT,TSLA" />
          <button id="optimize-btn" className="btn" onClick={optimize} disabled={loading}>
            {loading ? 'CALCULATING...' : '⚡ OPTIMIZE'}
          </button>
        </div>
        <p style={{ marginTop: 8, fontSize: '0.75rem', color: 'var(--muted)' }}>
          Allocates capital using inverse-volatility weighting to maximize risk-adjusted returns (lower volatility assets get larger allocation).
        </p>
      </div>
      {result && !result.error && (
        <div className="panel fade-up">
          <div className="section-title">Optimal Portfolio Weights</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginTop: 8 }}>
            {weightArr.map(([t, w], i) => (
              <div key={t} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <span style={{ fontFamily: 'var(--mono)', fontWeight: 700, width: 60, color: 'white' }}>{t}</span>
                <div style={{ flex: 1, background: 'rgba(255,255,255,0.05)', borderRadius: 4, height: 24, overflow: 'hidden' }}>
                  <div style={{ height: '100%', width: `${w}%`, background: colors[i % colors.length], borderRadius: 4, display: 'flex', alignItems: 'center', paddingLeft: 8, transition: 'width 1s ease' }}>
                    <span style={{ fontFamily: 'var(--mono)', fontSize: '0.75rem', color: '#070b12', fontWeight: 700 }}>{w}%</span>
                  </div>
                </div>
                <span style={{ fontFamily: 'var(--mono)', fontSize: '0.85rem', color: colors[i % colors.length], width: 50, textAlign: 'right' }}>{w}%</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function BacktestTab() {
  const [ticker, setTicker] = useState('AAPL');
  const [period, setPeriod] = useState('1y');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  const run = async () => {
    setLoading(true); setData(null);
    try {
      const res = await axios.get(`${API}/api/backtest/${ticker}?period=${period}`);
      setData(res.data);
    } catch { }
    setLoading(false);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div className="panel">
        <div className="section-title"><BarChart2 size={12} /> Strategy Backtester</div>
        <div style={{ display: 'flex', gap: 12, marginTop: 12 }}>
          <input id="backtest-ticker" className="input" value={ticker}
            onChange={e => setTicker(e.target.value.toUpperCase())} placeholder="Ticker" style={{ width: 120 }} />
          <select id="backtest-period" className="input" value={period} onChange={e => setPeriod(e.target.value)}
            style={{ background: 'rgba(0,0,0,0.3)', color: 'white' }}>
            <option value="6mo">6 Months</option>
            <option value="1y">1 Year</option>
            <option value="2y">2 Years</option>
            <option value="5y">5 Years</option>
          </select>
          <button id="run-backtest-btn" className="btn" onClick={run} disabled={loading}>
            {loading ? 'RUNNING...' : '▶ RUN BACKTEST'}
          </button>
        </div>
      </div>

      {data && !data.error && (
        <>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 12 }} className="fade-up">
            <StatCard label="Total Return" value={`${data.total_return_pct > 0 ? '+' : ''}${data.total_return_pct}%`} color={data.total_return_pct > 0 ? 'var(--green)' : 'var(--red)'} />
            <StatCard label="Final Equity" value={`$${data.end_equity.toLocaleString()}`} color="white" />
            <StatCard label="Sharpe Ratio" value={data.sharpe_ratio} color={data.sharpe_ratio > 1 ? 'var(--green)' : data.sharpe_ratio > 0 ? 'var(--amber)' : 'var(--red)'} />
            <StatCard label="Max Drawdown" value={`-${data.max_drawdown_pct}%`} color="var(--red)" />
            <StatCard label="Win Rate" value={`${data.win_rate}%`} color={data.win_rate > 50 ? 'var(--green)' : 'var(--red)'} />
          </div>
          <div className="panel fade-up">
            <div className="section-title">Buy-and-Hold Equity Curve — {data.ticker} ({data.period})</div>
            <ResponsiveContainer width="100%" height={260}>
              <AreaChart data={data.equity_curve} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="equityGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="var(--green)" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="var(--green)" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="date" tick={{ fontFamily: 'var(--mono)', fontSize: 9, fill: 'var(--muted)' }} tickCount={6} />
                <YAxis tick={{ fontFamily: 'var(--mono)', fontSize: 9, fill: 'var(--muted)' }} width={70} tickFormatter={v => `$${v.toLocaleString()}`} />
                <Tooltip contentStyle={{ background: '#0d1421', border: '1px solid var(--border)', fontFamily: 'var(--mono)', fontSize: 11 }} formatter={v => [`$${v.toLocaleString()}`, 'Equity']} />
                <ReferenceLine y={10000} stroke="rgba(255,255,255,0.1)" strokeDasharray="4 4" />
                <Area type="monotone" dataKey="equity" stroke="var(--green)" strokeWidth={2} fill="url(#equityGrad)" dot={false} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </>
      )}
    </div>
  );
}

function AuditTab() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    axios.get(`${API}/api/audit`).then(res => {
      setLogs(res.data.logs || []);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div className="panel" style={{ padding: '12px 20px' }}>
        <div className="section-title" style={{ margin: 0 }}><FileText size={12} /> Shariah Audit Log — {logs.length} entries</div>
      </div>
      <div className="panel fade-up" style={{ padding: 0 }}>
        {loading ? (
          <div style={{ padding: 20 }}>{[...Array(5)].map((_, i) => <Skeleton key={i} h={40} />)}</div>
        ) : logs.length === 0 ? (
          <div style={{ padding: 40, textAlign: 'center', color: 'var(--muted)', fontFamily: 'var(--mono)', fontSize: '0.85rem' }}>
            No audit entries found. Run the bot to generate audit records.
          </div>
        ) : (
          <div className="table-responsive"><table className="data-table">
            <thead>
              <tr>
                {Object.keys(logs[0] || {}).map(k => <th key={k}>{k}</th>)}
              </tr>
            </thead>
            <tbody>
              {logs.map((row, i) => (
                <tr key={i}>
                  {Object.values(row).map((v, j) => (
                    <td key={j}>{String(v ?? '—')}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table></div>
        )}
      </div>
    </div>
  );
}

// ─── Watchlist Strip ─────────────────────────────────────────

function WatchlistStrip() {
  const [items, setItems] = useState([]);
  useEffect(() => {
    const load = () => axios.get(`${API}/api/watchlist`).then(r => setItems(r.data.watchlist || [])).catch(() => {});
    load();
    const id = setInterval(load, 15000);
    return () => clearInterval(id);
  }, []);

  if (items.length === 0) return null;

  return (
    <div className="ticker-strip-wrapper" style={{ borderBottom: '1px solid var(--border)', padding: '6px 24px', background: 'rgba(0,0,0,0.3)' }}>
      <div className="ticker-strip">
        {items.map(t => (
          <div key={t.ticker} className="ticker-item">
            <span className="ticker-symbol">{t.ticker}</span>
            <span className="ticker-price">${t.price?.toFixed(2) ?? '—'}</span>
            <span className={`ticker-change ${t.change_pct >= 0 ? 'up' : 'down'}`}>
              {t.change_pct >= 0 ? '+' : ''}{t.change_pct?.toFixed(2)}%
            </span>
          </div>
        ))}
        {items.map(t => (
          <div key={`${t.ticker}-dup`} className="ticker-item">
            <span className="ticker-symbol">{t.ticker}</span>
            <span className="ticker-price">${t.price?.toFixed(2) ?? '—'}</span>
            <span className={`ticker-change ${t.change_pct >= 0 ? 'up' : 'down'}`}>
              {t.change_pct >= 0 ? '+' : ''}{t.change_pct?.toFixed(2)}%
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Simulator Tab ──────────────────────────────────────────

function SimulatorTab({ refreshPortfolio, portfolio }) {
  const [equity, setEquity] = useState(portfolio.equity || 10000);
  const [strategy, setStrategy] = useState(portfolio.active_strategy || 'ai_quant');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (portfolio.equity) setEquity(portfolio.equity);
    if (portfolio.active_strategy) setStrategy(portfolio.active_strategy);
  }, [portfolio]);

  const handleSimulate = async () => {
    setSaving(true);
    try {
      await axios.post(`${API}/api/portfolio/config`, { equity: parseFloat(equity), strategy });
      await refreshPortfolio();
    } catch (e) {
      console.error(e);
    }
    setSaving(false);
  };

  return (
    <div className="fade-up" style={{ padding: '20px' }}>
      <h2 style={{ marginBottom: '24px', display: 'flex', alignItems: 'center', gap: 10 }}>
        <Activity color="var(--green)" /> Portfolio Strategy Simulator
      </h2>
      <div className="panel" style={{ maxWidth: '600px', display: 'flex', flexDirection: 'column', gap: 24 }}>
        <div>
          <div className="label">Initial Equity Capital ($)</div>
          <input 
            type="number" 
            className="input" 
            style={{ width: '100%', fontSize: '1.2rem', padding: '12px' }} 
            value={equity} 
            onChange={e => setEquity(e.target.value)} 
          />
        </div>
        <div>
          <div className="label">Trading Strategy Engine</div>
          <select 
            className="input" 
            style={{ width: '100%', fontSize: '1rem', padding: '12px', background: 'var(--bg)', color: 'white' }}
            value={strategy}
            onChange={e => setStrategy(e.target.value)}
          >
            <option value="ai_quant">AI Quant Model (Balanced - Default)</option>
            <option value="trend_following">Trend Following (High Growth, Low Win Rate)</option>
            <option value="mean_reversion">Mean Reversion (High Win Rate, Low Growth)</option>
          </select>
        </div>
        <button 
          className="btn" 
          style={{ width: '100%', padding: '16px', fontSize: '1rem', background: 'var(--green)', color: '#000', marginTop: 10 }}
          onClick={handleSimulate}
          disabled={saving}
        >
          {saving ? 'SIMULATING...' : 'RUN SIMULATION & UPDATE PORTFOLIO'}
        </button>
      </div>
    </div>
  );
}

// ─── Journal / P&L Tab ──────────────────────────────────────

function JournalTab({ portfolio }) {
  const [journal, setJournal] = useState(null);
  const [form, setForm] = useState({ ticker: '', action: 'BUY', price: '', quantity: '', signal: '', notes: '' });
  const [exitPrice, setExitPrice] = useState({});
  const [telegram, setTelegram] = useState({ bot_token: '', chat_id: '' });
  const [tgStatus, setTgStatus] = useState('');
  const [alpaca, setAlpaca] = useState({ api_key: '', secret_key: '' });
  const [alpacaStatus, setAlpacaStatus] = useState('');
  const [submitting, setSubmitting] = useState(false);
  
  // Kelly Sizer State
  const [kellyTicker, setKellyTicker] = useState('');
  const [kellyConviction, setKellyConviction] = useState(65);
  const [kellyRes, setKellyRes] = useState(null);
  const [kellyLoading, setKellyLoading] = useState(false);

  const load = () => axios.get(`${API}/api/journal`).then(r => setJournal(r.data)).catch(() => {});
  useEffect(() => { load(); }, []);

  const handleLogTrade = async () => {
    setSubmitting(true);
    try {
      await axios.post(`${API}/api/journal/trade`, { ...form, price: parseFloat(form.price), quantity: parseFloat(form.quantity) });
      setForm({ ticker: '', action: 'BUY', price: '', quantity: '', signal: '', notes: '' });
      load();
    } catch (e) { console.error(e); }
    setSubmitting(false);
  };

  const handleClose = async (tradeId) => {
    const ep = parseFloat(exitPrice[tradeId]);
    if (!ep) return;
    await axios.post(`${API}/api/journal/trade/${tradeId}/close`, { exit_price: ep });
    load();
  };

  const handleSaveTelegram = async () => {
    setTgStatus('Saving...');
    await axios.post(`${API}/api/telegram/config`, telegram);
    setTgStatus('Saved!');
  };

  const handleSaveAlpaca = async () => {
    setAlpacaStatus('Saving keys...');
    await axios.post(`${API}/api/alpaca/config`, alpaca);
    setAlpacaStatus('Keys Secured!');
  };

  const handleTestTelegram = async () => {
    setTgStatus('Sending test...');
    const r = await axios.post(`${API}/api/telegram/test`);
    setTgStatus(r.data.status || r.data.error || 'Done');
  };

  const handleCalculateKelly = async () => {
    if (!kellyTicker) return;
    setKellyLoading(true);
    try {
      const eq = summary.current_equity || portfolio.equity || 10000;
      const res = await axios.get(`${API}/api/kelly?ticker=${kellyTicker}&equity=${eq}&conviction=${kellyConviction}`);
      setKellyRes(res.data);
    } catch (e) { console.error(e); }
    setKellyLoading(false);
  };

  const summary = journal?.summary || {};
  const curve = journal?.equity_curve || [];
  const trades = journal?.trades || [];

  return (
    <div className="fade-up" style={{ padding: 20, display: 'flex', flexDirection: 'column', gap: 24 }}>
      <h2 style={{ display: 'flex', alignItems: 'center', gap: 10 }}><TrendingUp color="var(--green)" /> Trade Journal & Position Sizer</h2>

      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 24 }}>
        
        {/* Left Column: Summary & Journal */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
          {/* Summary Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
            {[
              { label: 'Current Equity', val: `$${(summary.current_equity || portfolio.equity || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}`, color: 'var(--green)' },
              { label: 'Total P&L', val: `${(summary.total_pnl || 0) >= 0 ? '+' : ''}$${(summary.total_pnl || 0).toFixed(2)}`, color: (summary.total_pnl || 0) >= 0 ? 'var(--green)' : 'var(--red)' },
              { label: 'Win Rate', val: `${summary.win_rate || 0}%`, color: 'var(--blue)' },
              { label: 'Open / Closed', val: `${summary.open_trades || 0} / ${summary.closed_trades || 0}`, color: 'var(--muted)' },
            ].map(c => (
              <div key={c.label} className="panel" style={{ padding: 16 }}>
                <div className="label">{c.label}</div>
                <div style={{ fontFamily: 'var(--mono)', fontSize: '1.3rem', color: c.color, marginTop: 6 }}>{c.val}</div>
              </div>
            ))}
          </div>

          {/* Equity Curve */}
          {curve.length > 1 && (
            <div className="panel">
              <div className="section-title"><Activity size={14} /> Equity Curve</div>
              <ResponsiveContainer width="100%" height={180}>
                <AreaChart data={curve}>
                  <defs>
                    <linearGradient id="jrnlGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="var(--green)" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="var(--green)" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="date" tick={{ fontSize: 10, fill: 'var(--muted)' }} />
                  <YAxis domain={['auto', 'auto']} tick={{ fontSize: 10, fill: 'var(--muted)' }} />
                  <Tooltip formatter={(v) => [`$${v.toLocaleString()}`, 'Equity']} contentStyle={{ background: '#0d1117', border: '1px solid var(--border)', fontSize: 12 }} />
                  <Area type="monotone" dataKey="equity" stroke="var(--green)" fill="url(#jrnlGrad)" strokeWidth={2} dot={false} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Log New Trade */}
          <div className="panel">
            <div className="section-title"><Zap size={14} /> Log New Trade</div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12 }}>
              <div>
                <div className="label">Ticker</div>
                <input className="input" style={{ width: '100%' }} placeholder="e.g. AAPL" value={form.ticker} onChange={e => setForm(f => ({ ...f, ticker: e.target.value.toUpperCase() }))} />
              </div>
              <div>
                <div className="label">Action</div>
                <select className="input" style={{ width: '100%', background: 'var(--bg)', color: 'white' }} value={form.action} onChange={e => setForm(f => ({ ...f, action: e.target.value }))}>
                  <option value="BUY">BUY</option>
                  <option value="SELL">SELL</option>
                </select>
              </div>
              <div>
                <div className="label">Entry Price ($)</div>
                <input className="input" style={{ width: '100%' }} type="number" placeholder="e.g. 175.50" value={form.price} onChange={e => setForm(f => ({ ...f, price: e.target.value }))} />
              </div>
              <div>
                <div className="label">Quantity (shares)</div>
                <input className="input" style={{ width: '100%' }} type="number" placeholder="e.g. 10" value={form.quantity} onChange={e => setForm(f => ({ ...f, quantity: e.target.value }))} />
              </div>
              <div>
                <div className="label">Signal (optional)</div>
                <input className="input" style={{ width: '100%' }} placeholder="e.g. STRONG BUY" value={form.signal} onChange={e => setForm(f => ({ ...f, signal: e.target.value }))} />
              </div>
              <div>
                <div className="label">Notes (optional)</div>
                <input className="input" style={{ width: '100%' }} placeholder="Reason for trade..." value={form.notes} onChange={e => setForm(f => ({ ...f, notes: e.target.value }))} />
              </div>
            </div>
            <button className="btn" style={{ marginTop: 14, background: 'var(--green)', color: '#000' }} onClick={handleLogTrade} disabled={submitting || !form.ticker || !form.price || !form.quantity}>
              {submitting ? 'LOGGING...' : '+ LOG TRADE'}
            </button>
          </div>
          
          {/* Trade History */}
          <div className="panel">
            <div className="section-title"><FileText size={14} /> Trade History</div>
            {trades.length === 0 ? <div style={{ color: 'var(--muted)', fontSize: '0.85rem' }}>No trades logged yet.</div> : (
              <div className="table-responsive"><table className="data-table">
                <thead>
                  <tr>
                    <th>Date</th><th>Ticker</th><th>Action</th><th>Entry $</th><th>Qty</th><th>Signal</th><th>Exit $</th><th>P&L</th><th>Close</th>
                  </tr>
                </thead>
                <tbody>
                  {trades.map(t => (
                    <tr key={t.id}>
                      <td style={{ fontSize: '0.7rem', color: 'var(--muted)' }}>{t.timestamp?.slice(0, 10)}</td>
                      <td style={{ fontWeight: 700 }}>{t.ticker}</td>
                      <td><span style={{ color: t.action === 'BUY' ? 'var(--green)' : 'var(--red)', fontFamily: 'var(--mono)', fontSize: '0.75rem' }}>{t.action}</span></td>
                      <td>${t.price?.toFixed(2)}</td>
                      <td>{t.quantity}</td>
                      <td style={{ fontSize: '0.7rem', color: 'var(--muted)' }}>{t.signal || '—'}</td>
                      <td>{t.exit_price ? `$${t.exit_price.toFixed(2)}` : '—'}</td>
                      <td style={{ color: t.pnl == null ? 'var(--muted)' : t.pnl >= 0 ? 'var(--green)' : 'var(--red)', fontFamily: 'var(--mono)' }}>
                        {t.pnl == null ? 'OPEN' : `${t.pnl >= 0 ? '+' : ''}$${t.pnl.toFixed(2)}`}
                      </td>
                      <td>
                        {t.open && (
                          <div style={{ display: 'flex', gap: 6 }}>
                            <input className="input" type="number" style={{ width: 80, fontSize: '0.75rem', padding: '4px 8px' }} placeholder="Exit $" value={exitPrice[t.id] || ''} onChange={e => setExitPrice(p => ({ ...p, [t.id]: e.target.value }))} />
                            <button className="btn" style={{ fontSize: '0.7rem', padding: '4px 10px' }} onClick={() => handleClose(t.id)}>CLOSE</button>
                          </div>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table></div>
            )}
          </div>
        </div>

        {/* Right Column: Kelly Sizer & Telegram */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
          {/* Kelly Position Sizer */}
          <div className="panel" style={{ borderColor: 'var(--blue)' }}>
            <div className="section-title" style={{ color: 'var(--blue)' }}><Crosshair size={14} /> Kelly Position Sizer</div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text)', marginBottom: 16 }}>
              Calculate the mathematically optimal position size to maximize growth while preventing ruin, based on AI conviction.
            </div>
            
            <div style={{ display: 'flex', gap: 12, marginBottom: 12 }}>
              <div style={{ flex: 1 }}>
                <div className="label">Ticker</div>
                <input className="input" style={{ width: '100%' }} placeholder="AAPL" value={kellyTicker} onChange={e => setKellyTicker(e.target.value.toUpperCase())} />
              </div>
              <div style={{ flex: 1 }}>
                <div className="label">AI Conviction %</div>
                <input className="input" style={{ width: '100%' }} type="number" value={kellyConviction} onChange={e => setKellyConviction(e.target.value)} />
              </div>
            </div>
            
            <button className="btn btn-blue" style={{ width: '100%' }} onClick={handleCalculateKelly} disabled={kellyLoading || !kellyTicker}>
              {kellyLoading ? 'CALCULATING...' : 'CALCULATE OPTIMAL SIZE'}
            </button>
            
            {kellyRes && !kellyRes.error && (
              <div style={{ marginTop: 16, background: 'rgba(59,130,246,0.1)', padding: 12, borderRadius: 8, border: '1px solid rgba(59,130,246,0.2)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                  <span style={{ fontSize: '0.8rem', color: 'var(--muted)' }}>Recommended Allocation:</span>
                  <span style={{ fontFamily: 'var(--mono)', color: 'var(--blue)', fontWeight: 'bold' }}>{kellyRes.recommended_allocation_pct}%</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                  <span style={{ fontSize: '0.8rem', color: 'var(--muted)' }}>Investment Amount:</span>
                  <span style={{ fontFamily: 'var(--mono)', color: 'white' }}>${kellyRes.recommended_dollars.toLocaleString()}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                  <span style={{ fontSize: '0.8rem', color: 'var(--muted)' }}>Recommended Shares:</span>
                  <span style={{ fontFamily: 'var(--mono)', color: 'white' }}>{kellyRes.recommended_shares} shares</span>
                </div>
                <hr style={{ border: 'none', borderTop: '1px solid rgba(255,255,255,0.1)', margin: '12px 0' }} />
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                  <span style={{ fontSize: '0.75rem', color: 'var(--green)' }}>Take Profit (+{kellyRes.take_profit_pct}%):</span>
                  <span style={{ fontFamily: 'var(--mono)', color: 'var(--green)', fontSize: '0.8rem' }}>+${kellyRes.target_gain_dollars}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ fontSize: '0.75rem', color: 'var(--red)' }}>Stop Loss (-{kellyRes.stop_loss_pct}%):</span>
                  <span style={{ fontFamily: 'var(--mono)', color: 'var(--red)', fontSize: '0.8rem' }}>-${kellyRes.max_loss_dollars}</span>
                </div>
              </div>
            )}
            {kellyRes && kellyRes.error && <div style={{ marginTop: 12, color: 'var(--red)', fontSize: '0.8rem' }}>Error: {kellyRes.error}</div>}
          </div>

          {/* Telegram Config */}
          <div className="panel">
            <div className="section-title"><Zap size={14} /> Telegram Alert Integration</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginBottom: 12 }}>
              <div>
                <div className="label">Bot Token</div>
                <input className="input" style={{ width: '100%' }} type="password" placeholder="1234567890:ABCDef..." value={telegram.bot_token} onChange={e => setTelegram(t => ({ ...t, bot_token: e.target.value }))} />
              </div>
              <div>
                <div className="label">Chat ID</div>
                <input className="input" style={{ width: '100%' }} placeholder="e.g. -1001234567890" value={telegram.chat_id} onChange={e => setTelegram(t => ({ ...t, chat_id: e.target.value }))} />
              </div>
            </div>
            <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
              <button className="btn" onClick={handleSaveTelegram}>SAVE CONFIG</button>
              <button className="btn btn-blue" onClick={handleTestTelegram}>SEND TEST</button>
            </div>
            {tgStatus && <div style={{ fontFamily: 'var(--mono)', fontSize: '0.75rem', marginTop: 10, color: tgStatus.includes('sent') || tgStatus.includes('Saved') ? 'var(--green)' : 'var(--amber)' }}>{tgStatus}</div>}
            <div style={{ marginTop: 12, fontSize: '0.75rem', color: 'var(--muted)', lineHeight: 1.7 }}>
              Auto-alerts are triggered when AI Conviction is ≥ 75%.
            </div>
          </div>

          {/* Alpaca API Config */}
          <div className="panel" style={{ borderColor: 'var(--green)' }}>
            <div className="section-title" style={{ color: 'var(--green)' }}><Zap size={14} /> Live Broker Integration (Alpaca)</div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text)', marginBottom: 16 }}>
              Connect your Alpaca Paper Trading account for fully autonomous Hedge Fund execution.
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginBottom: 12 }}>
              <div>
                <div className="label">API Key</div>
                <input className="input" style={{ width: '100%' }} type="password" placeholder="PKBXXXXXXX..." value={alpaca.api_key} onChange={e => setAlpaca(a => ({ ...a, api_key: e.target.value }))} />
              </div>
              <div>
                <div className="label">Secret Key</div>
                <input className="input" style={{ width: '100%' }} type="password" placeholder="xxxxxxxxxxxxxx" value={alpaca.secret_key} onChange={e => setAlpaca(a => ({ ...a, secret_key: e.target.value }))} />
              </div>
            </div>
            <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
              <button className="btn" style={{ background: 'var(--green)', color: '#000' }} onClick={handleSaveAlpaca}>CONNECT BROKER</button>
              {alpacaStatus && <span style={{ fontFamily: 'var(--mono)', fontSize: '0.75rem', color: 'var(--green)' }}>{alpacaStatus}</span>}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Sidebar Portfolio Stats ─────────────────────────────────

function Sidebar({ portfolio }) {
  return (
    <div className="sidebar">
      <div className="label" style={{ marginBottom: 4 }}>Portfolio</div>
      <div className="stat-card">
        <div className="label">Total Equity</div>
        <div className="val-lg" style={{ fontSize: '1.4rem', marginTop: 4 }}>${portfolio.equity?.toLocaleString(undefined, { minimumFractionDigits: 2 })}</div>
        <div style={{ fontFamily: 'var(--mono)', fontSize: '0.8rem', color: 'var(--green)', marginTop: 4 }}>{portfolio.daily_change}</div>
      </div>
      {[
        { label: 'Win Rate', val: portfolio.win_rate, color: 'var(--green)' },
        { label: 'Sharpe Ratio', val: portfolio.sharpe_ratio, color: 'var(--blue)' },
        { label: 'Max Drawdown', val: portfolio.max_drawdown, color: 'var(--red)' },
        { label: 'Total Trades', val: portfolio.total_trades, color: 'var(--muted)' },
      ].map(s => <StatCard key={s.label} label={s.label} value={s.val} color={s.color} />)}
    </div>
  );
}

// ─── Main App ────────────────────────────────────────────────

export default function App() {
  const [tab, setTab] = useState('home');
  const [portfolio, setPortfolio] = useState({ equity: 0, daily_change: '+0%', win_rate: '0%', sharpe_ratio: '0', max_drawdown: '0%', total_trades: 0 });

  const refreshPortfolio = () => {
    return axios.get(`${API}/api/portfolio`).then(r => setPortfolio(r.data)).catch(() => {});
  };

  useEffect(() => {
    refreshPortfolio();
    const id = setInterval(refreshPortfolio, 30000);
    return () => clearInterval(id);
  }, []);

  const TABS = [
    { id: 'home', label: '🏠 DASHBOARD', icon: Home },
    { id: 'terminal', label: '⚡ TERMINAL', icon: Crosshair },
    { id: 'signals', label: '📡 SIGNALS', icon: Zap },
    { id: 'journal', label: '📒 JOURNAL', icon: TrendingUp },
    { id: 'simulator', label: '🎛️ SIMULATOR', icon: Activity },
    { id: 'optimizer', label: '📐 OPTIMIZER', icon: Target },
    { id: 'backtest', label: '📊 BACKTEST', icon: BarChart2 },
    { id: 'audit', label: '📋 AUDIT LOG', icon: FileText },
  ];

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Navbar */}
      <nav className="navbar">
        <div className="logo" style={{ gap: '16px', alignItems: 'center' }}>
          <img src={logoImg} alt="MHT Logo" style={{ height: '54px', width: 'auto', filter: 'drop-shadow(0 0 10px rgba(255,255,255,0.7)) drop-shadow(0 0 2px rgba(255,255,255,0.8))' }} />
          MyHalal<span>Trade</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontFamily: 'var(--mono)', fontSize: '0.7rem', color: 'var(--muted)' }}>
            <span className="live-dot" /> LIVE
          </div>
          <div className="tabs">
            {TABS.map(t => (
              <button key={t.id} id={`tab-${t.id}`} className={`tab ${tab === t.id ? 'active' : ''}`} onClick={() => setTab(t.id)}>
                {t.label}
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* Moving Ticker below Navbar */}
      <WatchlistStrip />

      {/* Body */}
      <div className="layout">
        <Sidebar portfolio={portfolio} />
        <div className="main-content">
          {tab === 'home' && <HomeTab />}
          {tab === 'terminal' && <TerminalTab portfolio={portfolio} />}
          {tab === 'signals' && <SignalsTab />}
          {tab === 'journal' && <JournalTab portfolio={portfolio} />}
          {tab === 'simulator' && <SimulatorTab refreshPortfolio={refreshPortfolio} portfolio={portfolio} />}
          {tab === 'optimizer' && <OptimizerTab />}
          {tab === 'backtest' && <BacktestTab />}
          {tab === 'audit' && <AuditTab />}
        </div>
      </div>
    </div>
  );
}
