import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  ShieldCheck, Activity, DollarSign, Crosshair, Search,
  TrendingUp, BarChart2, FileText, Zap, RefreshCw,
  ArrowUpRight, ArrowDownRight, Minus, Target, AlertTriangle
} from 'lucide-react';
import axios from 'axios';
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer,
  AreaChart, Area, ReferenceLine
} from 'recharts';
import { createChart } from 'lightweight-charts';
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

// ─── TradingView Chart Component ─────────────────────────────

function TradingChart({ ticker }) {
  const chartContainerRef = useRef();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!ticker) return;
    
    let chart;
    const fetchAndRender = async () => {
      setLoading(true); setError(null);
      try {
        const res = await axios.get(`${API}/api/chart/${ticker}`);
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

        const candlestickSeries = chart.addCandlestickSeries({
          upColor: '#00ffaa', downColor: '#ff4d4d', borderVisible: false,
          wickUpColor: '#00ffaa', wickDownColor: '#ff4d4d',
        });
        candlestickSeries.setData(data);

        const volumeSeries = chart.addHistogramSeries({
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
        setError('Failed to load chart data');
      } finally {
        setLoading(false);
      }
    };
    
    fetchAndRender();
    return () => { if (chart) chart.remove(); };
  }, [ticker]);

  return (
    <div className="panel fade-up" style={{ padding: '4px', height: '400px', display: 'flex', flexDirection: 'column' }}>
      <div style={{ padding: '12px 16px', display: 'flex', justifyContent: 'space-between' }}>
        <span className="section-title" style={{ margin: 0 }}><Activity size={14} /> Interactive Chart — {ticker}</span>
        {loading && <span style={{ color: 'var(--amber)', fontSize: '0.8rem' }}>Loading...</span>}
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
          <table className="data-table">
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
          </table>
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
          <table className="data-table">
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
          </table>
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
    <div style={{ borderBottom: '1px solid var(--border)', padding: '6px 24px', background: 'rgba(0,0,0,0.3)' }}>
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
  const [tab, setTab] = useState('terminal');
  const [portfolio, setPortfolio] = useState({ equity: 0, daily_change: '+0%', win_rate: '0%', sharpe_ratio: '0', max_drawdown: '0%', total_trades: 0 });

  useEffect(() => {
    axios.get(`${API}/api/portfolio`).then(r => setPortfolio(r.data)).catch(() => {});
    const id = setInterval(() => axios.get(`${API}/api/portfolio`).then(r => setPortfolio(r.data)).catch(() => {}), 30000);
    return () => clearInterval(id);
  }, []);

  const TABS = [
    { id: 'terminal', label: '⚡ TERMINAL', icon: Crosshair },
    { id: 'signals', label: '📡 SIGNALS', icon: Zap },
    { id: 'optimizer', label: '📐 OPTIMIZER', icon: Target },
    { id: 'backtest', label: '📊 BACKTEST', icon: BarChart2 },
    { id: 'audit', label: '📋 AUDIT LOG', icon: FileText },
  ];

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Navbar */}
      <nav className="navbar">
        <div className="logo">
          <ShieldCheck size={20} color="var(--green)" />
          AlphaQuant <span>Shariah</span>
        </div>
        <WatchlistStrip />
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

      {/* Body */}
      <div className="layout">
        <Sidebar portfolio={portfolio} />
        <div className="main-content">
          {tab === 'terminal' && <TerminalTab portfolio={portfolio} />}
          {tab === 'signals' && <SignalsTab />}
          {tab === 'optimizer' && <OptimizerTab />}
          {tab === 'backtest' && <BacktestTab />}
          {tab === 'audit' && <AuditTab />}
        </div>
      </div>
    </div>
  );
}
