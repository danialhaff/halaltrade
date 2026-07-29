import uvicorn
import asyncio
import sqlite3
import os
import pandas as pd
import yfinance as yf
import numpy as np
import requests_cache
import concurrent.futures
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Install global caching for all HTTP requests (e.g. yfinance, news). Cache lasts 5 minutes.
requests_cache.install_cache('alphaquant_cache', expire_after=300)

from core.config import DB_PATH
from screener.shariah_engine import ShariahEngine, MAX_DEBT_RATIO, MAX_CASH_RATIO, MAX_RECEIVABLES_RATIO
from data.yfinance_provider import YFinanceProvider
from strategy.multi_factor_engine import MultiFactorEngine
from strategy.quant_math import QuantMathEngine

app = FastAPI(title="AlphaQuant Institutional API", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

provider = YFinanceProvider()
shariah_engine = ShariahEngine(provider)
multi_engine = MultiFactorEngine(provider)
quant_math = QuantMathEngine()

# Expanded Global Halal watchlist (US, China ADRs, Malaysia)
WATCHLIST = [
    # US Tech & Global Giants
    "AAPL", "NVDA", "MSFT", "TSLA", "AMZN", "GOOGL", "META", "AVGO", "ADBE", "CRM", "AMD", "QCOM", "ASML",
    # China (ADRs)
    "BABA", "PDD", "JD", "BIDU", "NTES", "LI",
    # Malaysia (Bursa - using .KL suffix)
    "5183.KL", # Petronas Chemicals
    "6033.KL", # Petronas Gas
    "5225.KL", # IHH Healthcare
    "0166.KL", # Inari
    "7277.KL", # Dialog
    "5168.KL", # Hartalega
    "7113.KL", # Top Glove
    "4707.KL", # Nestle Malaysia
    "4197.KL", # Sime Darby
    "1961.KL", # IOI Corp
    # Other Shariah-Compliant US / Global 
    "JNJ", "PFE", "NKE", "PEP", "KO", "MCD", "SBUX", "LULU", "INTC",
    # Crypto (Shariah Scholars allowed list)
    "BTC-USD", "ETH-USD",
    # Islamic Indices & Commodities
    "SPUS", "HLAL", "UMMA", "SPSK", "GLD", "SLV"
]


def get_db():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


# ─────────────────────────────────────────────────────────────
# ENDPOINT 1: Deep Analysis (Terminal Tab)
# ─────────────────────────────────────────────────────────────
@app.get("/api/analyze/{ticker}")
def analyze_ticker(ticker: str):
    ticker = ticker.upper()
    try:
        is_compliant = shariah_engine.screen_stock(ticker)
        ratios = provider.get_financial_ratios(ticker)
        analysis = multi_engine.generate_analysis(ticker, 'stock')
        var_data = quant_math.calculate_var(ticker, portfolio_value=1000.0)
        mc_data = quant_math.monte_carlo_simulation(ticker, days=30, simulations=300)

        return {
            "ticker": ticker,
            "shariah": {
                "is_compliant": is_compliant,
                "debt_ratio": ratios.get('debt_to_mcap', 0),
                "cash_ratio": ratios.get('cash_to_mcap', 0),
                "receivables_ratio": ratios.get('receivables_to_mcap', 0),
                "max_debt": MAX_DEBT_RATIO,
                "max_cash": MAX_CASH_RATIO,
                "max_receivables": MAX_RECEIVABLES_RATIO,
            },
            "ai_signal": analysis,
            "risk_model": var_data,
            "monte_carlo": mc_data,
        }
    except Exception as e:
        return {"error": str(e)}


USER_PORTFOLIO_CONFIG = {
    "equity": 10000.0,
    "strategy": "ai_quant"
}

class PortfolioConfig(BaseModel):
    equity: float
    strategy: str

@app.post("/api/portfolio/config")
def update_portfolio_config(config: PortfolioConfig):
    global USER_PORTFOLIO_CONFIG
    USER_PORTFOLIO_CONFIG["equity"] = config.equity
    USER_PORTFOLIO_CONFIG["strategy"] = config.strategy
    return {"status": "success", "config": USER_PORTFOLIO_CONFIG}

# ─────────────────────────────────────────────────────────────
# ENDPOINT 2: Portfolio Stats
# ─────────────────────────────────────────────────────────────
@app.get("/api/portfolio")
def get_portfolio_stats():
    global USER_PORTFOLIO_CONFIG
    conn = get_db()
    try:
        df = pd.read_sql_query("SELECT * FROM trade_journal", conn)
        total_trades = len(df)
        equity = USER_PORTFOLIO_CONFIG["equity"]
        strat = USER_PORTFOLIO_CONFIG["strategy"]
        
        win_rate = "0.0%"
        sharpe = "0.00"
        dd = "0.0%"
        daily = "0.00%"
        
        if total_trades > 0:
            closed = df[df['pnl'].notnull()]
            if len(closed) > 0:
                wins = len(closed[closed['pnl'] > 0])
                win_rate = f"{(wins / len(closed)) * 100:.1f}%"
                
                avg_pnl = closed['pnl'].mean()
                std_pnl = closed['pnl'].std()
                if std_pnl > 0:
                    sharpe = f"{(avg_pnl / std_pnl):.2f}"
                
                last_pnl = closed.iloc[-1]['pnl']
                daily = f"{'+' if last_pnl >= 0 else ''}{(last_pnl / equity) * 100:.2f}%"
        
        return {
            "equity": equity,
            "daily_change": daily,
            "win_rate": win_rate,
            "sharpe_ratio": sharpe,
            "max_drawdown": dd,
            "total_trades": total_trades,
            "active_strategy": strat
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()


import time
SIGNALS_CACHE = {"data": None, "timestamp": 0}

# ─────────────────────────────────────────────────────────────
# ENDPOINT 3: Live Signal Scanner (Signals Tab)
# ─────────────────────────────────────────────────────────────
@app.get("/api/signals")
def get_signals():
    global SIGNALS_CACHE
    if time.time() - SIGNALS_CACHE["timestamp"] < 300 and SIGNALS_CACHE["data"] is not None:
        return SIGNALS_CACHE["data"]

    def fetch_signal(ticker):
        try:
            # Route to the correct screening logic based on asset type
            from core.config import ETF_WHITELIST
            if "-USD" in ticker:
                is_compliant = shariah_engine.screen_crypto(ticker)
                asset_type = 'crypto'
            elif ticker in ETF_WHITELIST:
                is_compliant = shariah_engine.screen_etf(ticker)
                asset_type = 'etf'
            else:
                is_compliant = shariah_engine.screen_stock(ticker)
                asset_type = 'stock'

            if not is_compliant:
                return {
                    "ticker": ticker, "signal": "HARAM", "conviction": 0,
                    "is_compliant": False, "technical_score": 0,
                    "fundamental_score": 0, "sentiment_score": 0,
                    "target_profit_pct": 0, "stop_loss_pct": 0,
                }
            
            # Use 'crypto' for ML features if it's crypto, else 'stock'
            analysis = multi_engine.generate_analysis(ticker, asset_type)
            return {
                "ticker": ticker,
                "signal": analysis["signal"],
                "conviction": analysis["conviction"],
                "is_compliant": True,
                "technical_score": analysis["technical_score"],
                "fundamental_score": analysis["fundamental_score"],
                "sentiment_score": analysis["sentiment_score"],
                "target_profit_pct": analysis.get("target_profit_pct", 0),
                "stop_loss_pct": analysis.get("stop_loss_pct", 0),
                "rsi": analysis["ta_data"].get("rsi"),
                "golden_cross": analysis["ta_data"].get("golden_cross"),
            }
        except Exception as e:
            return {"ticker": ticker, "signal": "ERROR", "conviction": 0, "error": str(e)}

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(fetch_signal, WATCHLIST))

    results.sort(key=lambda x: x.get("conviction", 0), reverse=True)
    res = {"signals": results, "count": len(results)}
    SIGNALS_CACHE["data"] = res
    SIGNALS_CACHE["timestamp"] = time.time()

    # Auto-fire Telegram alerts for STRONG BUY signals
    def auto_alert():
        token = TELEGRAM_RUNTIME_CONFIG.get("token")
        chat_id = TELEGRAM_RUNTIME_CONFIG.get("chat_id")
        if not token or not chat_id:
            return
        import requests as req
        strong_buys = [s for s in results if s.get("signal") in ("STRONG BUY", "BUY") and s.get("conviction", 0) >= 75 and s.get("is_compliant")]
        for s in strong_buys[:3]:  # Max 3 alerts at once
            try:
                icon = "🚀" if s["signal"] == "STRONG BUY" else "📈"
                msg = (
                    f"{icon} MyHalalTrade AUTO ALERT\n\n"
                    f"Asset: {s['ticker']}\n"
                    f"Signal: {s['signal']}\n"
                    f"Conviction: {s['conviction']}%\n"
                    f"Tech Score: {s.get('technical_score', 0)}%  |  Fund Score: {s.get('fundamental_score', 0)}%\n\n"
                    f"Open MyHalalTrade to review and act."
                )
                req.post(f"https://api.telegram.org/bot{token}/sendMessage",
                         json={"chat_id": chat_id, "text": msg}, timeout=10)
            except:
                pass
    import threading
    threading.Thread(target=auto_alert, daemon=True).start()

    return res


WATCHLIST_CACHE = {"data": None, "timestamp": 0}

# ─────────────────────────────────────────────────────────────
# ENDPOINT 4: Global Watchlist Prices
# ─────────────────────────────────────────────────────────────
@app.get("/api/watchlist")
def get_watchlist():
    global WATCHLIST_CACHE
    if time.time() - WATCHLIST_CACHE["timestamp"] < 30 and WATCHLIST_CACHE["data"] is not None:
        return WATCHLIST_CACHE["data"]

    import math
    def clean_float(v):
        try:
            val = float(v)
            return 0.0 if math.isnan(val) or math.isinf(val) else val
        except:
            return 0.0

    def fetch_market_data(ticker):
        try:
            t = yf.Ticker(ticker)
            info = t.fast_info
            hist = t.history(period="2d")
            if len(hist) >= 2:
                prev_close = clean_float(hist['Close'].iloc[-2])
                curr_price = clean_float(hist['Close'].iloc[-1])
                change_pct = round((curr_price - prev_close) / prev_close * 100, 2) if prev_close > 0 else 0.0
            else:
                curr_price = clean_float(getattr(info, 'last_price', 0) or 0)
                change_pct = 0.0

            return {
                "ticker": ticker,
                "price": round(curr_price, 2),
                "change_pct": clean_float(change_pct),
                "volume": int(clean_float(getattr(info, 'three_month_average_volume', 0) or 0)),
                "market_cap": int(clean_float(getattr(info, 'market_cap', 0) or 0)),
                "week52_high": round(clean_float(getattr(info, 'fifty_two_week_high', 0) or 0), 2),
                "week52_low": round(clean_float(getattr(info, 'fifty_two_week_low', 0) or 0), 2),
            }
        except Exception as e:
            return {"ticker": ticker, "price": 0, "change_pct": 0, "error": str(e)}

    data = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        raw_data = list(executor.map(fetch_market_data, WATCHLIST))
        data = [d for d in raw_data if "error" not in d]

    result = {"watchlist": data, "count": len(data)}
    WATCHLIST_CACHE["data"] = result
    WATCHLIST_CACHE["timestamp"] = time.time()
    return result

# ─────────────────────────────────────────────────────────────
# ENDPOINT 5: Portfolio Optimizer (Optimizer Tab)
# ─────────────────────────────────────────────────────────────
@app.get("/api/optimize")
def optimize_portfolio(tickers: str = "AAPL,NVDA,MSFT"):
    ticker_list = [t.strip().upper() for t in tickers.split(",") if t.strip()]
    result = quant_math.calculate_optimal_weights(ticker_list)
    return result


# ─────────────────────────────────────────────────────────────
# ENDPOINT 6: Backtest (Backtest Tab)
# ─────────────────────────────────────────────────────────────
@app.get("/api/backtest/{ticker}")
def backtest_ticker(ticker: str, period: str = "1y"):
    ticker = ticker.upper()
    try:
        df = yf.download(ticker, period=period, progress=False, auto_adjust=True)
        if df.empty:
            return {"error": "No data"}
        close = df['Close'].squeeze().values.astype(float)
        dates = [str(d.date()) for d in df.index]
        returns = np.diff(close) / close[:-1]

        # Simple buy-and-hold equity curve (starting $10,000)
        equity = [10000.0]
        for r in returns:
            equity.append(round(equity[-1] * (1 + r), 2))

        # Sharpe Ratio
        daily_rf = 0.05 / 252
        excess = returns - daily_rf
        sharpe = round(float(np.mean(excess) / np.std(excess) * np.sqrt(252)), 2) if np.std(excess) > 0 else 0

        # Max Drawdown
        peak = equity[0]
        max_dd = 0
        for e in equity:
            if e > peak:
                peak = e
            dd = (peak - e) / peak
            if dd > max_dd:
                max_dd = dd

        # Win Rate
        win_rate = round(float(np.mean(returns > 0) * 100), 1)

        equity_curve = [{"date": dates[i], "equity": equity[i]} for i in range(len(dates))]

        return {
            "ticker": ticker,
            "period": period,
            "start_equity": 10000,
            "end_equity": round(equity[-1], 2),
            "total_return_pct": round((equity[-1] - 10000) / 10000 * 100, 2),
            "sharpe_ratio": sharpe,
            "max_drawdown_pct": round(max_dd * 100, 2),
            "win_rate": win_rate,
            "equity_curve": equity_curve,
        }
    except Exception as e:
        return {"error": str(e)}


# ─────────────────────────────────────────────────────────────
# ENDPOINT 7: Audit Log (Audit Tab)
# ─────────────────────────────────────────────────────────────
@app.get("/api/audit")
def get_audit_log(limit: int = 50):
    conn = get_db()
    try:
        try:
            df = pd.read_sql_query(
                f"SELECT * FROM shariah_audit ORDER BY timestamp DESC LIMIT {limit}", conn
            )
            return {"logs": df.to_dict(orient='records')}
        except Exception:
            try:
                df = pd.read_sql_query(
                    f"SELECT * FROM paper_trades ORDER BY timestamp DESC LIMIT {limit}", conn
                )
                return {"logs": df.to_dict(orient='records')}
            except Exception as e2:
                return {"logs": [], "error": str(e2)}
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────
# ENDPOINT 8: TradingView Chart Data (Chart Tab)
# ─────────────────────────────────────────────────────────────
@app.get("/api/chart/{ticker}")
def get_chart_data(ticker: str, period: str = "6mo"):
    try:
        interval = "1d"
        if period == "1wk":
            interval = "15m"
        elif period == "1mo":
            interval = "1h"
            
        df = yf.download(ticker, period=period, interval=interval, progress=False, auto_adjust=True)
        if df.empty:
            return {"error": "No chart data found"}
            
        # Lightweight charts requires strictly ascending, unique dates.
        chart_data = []
        seen_dates = set()
        
        for date, row in df.iterrows():
            # If intraday, use unix timestamp. If daily, use YYYY-MM-DD string.
            if interval in ["15m", "1h", "5m"]:
                time_val = int(date.timestamp())
                uniq_key = str(time_val)
            else:
                time_val = date.strftime('%Y-%m-%d')
                uniq_key = time_val
                
            if uniq_key in seen_dates:
                continue
                
            try:
                o = float(row['Open'].squeeze())
                h = float(row['High'].squeeze())
                l = float(row['Low'].squeeze())
                c = float(row['Close'].squeeze())
                v = float(row['Volume'].squeeze())
                
                # lightweight-charts will crash if there are NaNs
                if np.isnan(o) or np.isnan(h) or np.isnan(l) or np.isnan(c):
                    continue
                    
                seen_dates.add(uniq_key)
                chart_data.append({
                    "time": time_val,
                    "open": o,
                    "high": h,
                    "low": l,
                    "close": c,
                    "value": v if not np.isnan(v) else 0.0
                })
            except Exception:
                continue
            
        chart_data.sort(key=lambda x: x['time'])
        return {"data": chart_data}
    except Exception as e:
        return {"error": str(e)}

# ─────────────────────────────────────────────────────────────
# ENDPOINT 9: WebSocket Live Price Stream
# ─────────────────────────────────────────────────────────────
@app.websocket("/ws/price/{ticker}")
async def websocket_price(websocket: WebSocket, ticker: str):
    await websocket.accept()
    ticker = ticker.upper()
    try:
        while True:
            try:
                t = yf.Ticker(ticker)
                hist = t.history(period="2d")
                if len(hist) >= 2:
                    prev = float(hist['Close'].iloc[-2])
                    curr = float(hist['Close'].iloc[-1])
                    change = round((curr - prev) / prev * 100, 2)
                    await websocket.send_json({
                        "ticker": ticker,
                        "price": round(curr, 2),
                        "change_pct": change,
                    })
            except Exception as e:
                await websocket.send_json({"error": str(e)})
            await asyncio.sleep(10)
    except WebSocketDisconnect:
        pass


# ─────────────────────────────────────────────────────────────
# ENDPOINT 7: Market Dashboard (Hedge Fund View)
# ─────────────────────────────────────────────────────────────
@app.get("/api/market/dashboard")
def get_market_dashboard():
    try:
        # 1. Volatility Index (VIX)
        vix_ticker = yf.Ticker('^VIX')
        vix_hist = vix_ticker.history(period="2d")
        if len(vix_hist) >= 2:
            prev_vix = float(vix_hist['Close'].iloc[-2])
            curr_vix = float(vix_hist['Close'].iloc[-1])
            vix_change = ((curr_vix - prev_vix) / prev_vix) * 100
        else:
            curr_vix, vix_change = 20.0, 0.0

        # 2. Top AI Picks (Scan Watchlist)
        signals_res = get_signals()
        
        # Filter only COMPLIANT and STRONG BUY or BUY signals
        valid_picks = [s for s in signals_res.get("signals", []) if s.get("is_compliant") and s.get("conviction", 0) > 50]
        valid_picks.sort(key=lambda x: x.get("conviction", 0), reverse=True)
        top_picks = valid_picks[:3]

        # 3. Market News (General)
        # Using S&P 500 (^GSPC) as a proxy for general macroeconomic news
        market_news = multi_engine.nlp.get_news_sentiment('^GSPC')

        return {
            "vix": {
                "value": round(curr_vix, 2),
                "change_pct": round(vix_change, 2),
                "status": "High Risk (Fear)" if curr_vix > 25 else "Moderate" if curr_vix > 15 else "Low Risk (Greed)"
            },
            "top_picks": top_picks,
            "market_news": market_news.get("headlines", [])[:5]
        }
    except Exception as e:
        return {"error": str(e)}

# ─────────────────────────────────────────────────────────────
# ENDPOINT 8: Upcoming IPOs (Live Scraper)
# ─────────────────────────────────────────────────────────────
IPO_CACHE = {"data": None, "timestamp": 0}

@app.get("/api/market/ipos")
def get_upcoming_ipos():
    global IPO_CACHE
    if time.time() - IPO_CACHE["timestamp"] < 3600 * 12 and IPO_CACHE["data"]:
        return {"ipos": IPO_CACHE["data"]}
        
    try:
        import requests
        from bs4 import BeautifulSoup
        res = requests.get('https://stockanalysis.com/ipos/calendar/', headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        soup = BeautifulSoup(res.text, 'lxml')
        rows = soup.select('table tbody tr')
        
        ipos = []
        for r in rows[:5]:
            cols = [td.text.strip() for td in r.find_all('td')]
            if len(cols) >= 8:
                ipos.append({
                    "company": cols[2].replace('\x80\x99', "'"),
                    "symbol": cols[1],
                    "expected_date": cols[0],
                    "est_valuation": cols[7] if cols[7] != "-" else "TBD",
                    "sector": "Various"
                })
        
        if ipos:
            IPO_CACHE["data"] = ipos
            IPO_CACHE["timestamp"] = time.time()
            return {"ipos": ipos}
    except Exception as e:
        print("IPO Scraper error:", e)
        
    # Fallback if scraper fails
    return {
        "ipos": [
            {"company": "Scraper Offline", "symbol": "ERR", "expected_date": "TBD", "est_valuation": "N/A", "sector": "N/A"}
        ]
    }


# ─────────────────────────────────────────────────────────────
# TRADE JOURNAL SETUP (P&L Tracker)
# ─────────────────────────────────────────────────────────────
def init_journal_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS trade_journal (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT DEFAULT (datetime('now')),
            ticker TEXT NOT NULL,
            action TEXT NOT NULL,
            price REAL NOT NULL,
            quantity REAL NOT NULL,
            conviction INTEGER,
            signal TEXT,
            notes TEXT,
            exit_price REAL,
            closed_at TEXT,
            pnl REAL
        )
    """)
    conn.commit()
    conn.close()

init_journal_db()

class TradeEntry(BaseModel):
    ticker: str
    action: str
    price: float
    quantity: float
    conviction: int = 0
    signal: str = ""
    notes: str = ""

class TradeExit(BaseModel):
    exit_price: float

# ─────────────────────────────────────────────────────────────
# ENDPOINT: Log a Manual Trade (Buy/Sell)
# ─────────────────────────────────────────────────────────────
@app.post("/api/journal/trade")
def log_trade(trade: TradeEntry):
    conn = get_db()
    try:
        conn.execute("""
            INSERT INTO trade_journal (ticker, action, price, quantity, conviction, signal, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (trade.ticker.upper(), trade.action.upper(), trade.price, trade.quantity,
              trade.conviction, trade.signal, trade.notes))
        conn.commit()
        return {"status": "success", "message": f"Trade logged: {trade.action} {trade.quantity} {trade.ticker} @ ${trade.price}"}
    finally:
        conn.close()

# ─────────────────────────────────────────────────────────────
# ENDPOINT: Close an Open Trade (Calculate P&L)
# ─────────────────────────────────────────────────────────────
@app.post("/api/journal/trade/{trade_id}/close")
def close_trade(trade_id: int, exit: TradeExit):
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM trade_journal WHERE id = ?", (trade_id,)).fetchone()
        if not row:
            return {"error": "Trade not found"}
        entry_price = row[4]
        quantity = row[5]
        pnl = round((exit.exit_price - entry_price) * quantity, 2)
        conn.execute("""
            UPDATE trade_journal SET exit_price = ?, closed_at = datetime('now'), pnl = ? WHERE id = ?
        """, (exit.exit_price, pnl, trade_id))
        conn.commit()
        return {"status": "success", "pnl": pnl, "trade_id": trade_id}
    finally:
        conn.close()

# ─────────────────────────────────────────────────────────────
# ENDPOINT: Get Full P&L Journal + Running Equity Curve
# ─────────────────────────────────────────────────────────────
@app.get("/api/journal")
def get_journal():
    conn = get_db()
    try:
        rows = conn.execute("""
            SELECT id, timestamp, ticker, action, price, quantity, conviction, signal, notes, exit_price, closed_at, pnl
            FROM trade_journal ORDER BY timestamp DESC
        """).fetchall()
        trades = []
        for r in rows:
            trades.append({
                "id": r[0], "timestamp": r[1], "ticker": r[2], "action": r[3],
                "price": r[4], "quantity": r[5], "conviction": r[6], "signal": r[7],
                "notes": r[8], "exit_price": r[9], "closed_at": r[10], "pnl": r[11],
                "open": r[9] is None
            })

        # Compute cumulative P&L equity curve
        starting_equity = USER_PORTFOLIO_CONFIG["equity"]
        closed = sorted([t for t in trades if not t["open"]], key=lambda x: x["closed_at"])
        equity_curve = [{"date": "Start", "equity": starting_equity}]
        running = starting_equity
        for t in closed:
            running = round(running + t["pnl"], 2)
            equity_curve.append({"date": t["closed_at"][:10], "equity": running})

        total_pnl = round(sum(t["pnl"] for t in trades if t["pnl"] is not None), 2)
        wins = [t for t in trades if t["pnl"] and t["pnl"] > 0]
        losses = [t for t in trades if t["pnl"] and t["pnl"] < 0]
        win_rate = round(len(wins) / max(len(wins) + len(losses), 1) * 100, 1)

        return {
            "trades": trades,
            "equity_curve": equity_curve,
            "summary": {
                "total_pnl": total_pnl,
                "win_rate": win_rate,
                "open_trades": len([t for t in trades if t["open"]]),
                "closed_trades": len(wins) + len(losses),
                "current_equity": round(starting_equity + total_pnl, 2)
            }
        }
    finally:
        conn.close()

# ─────────────────────────────────────────────────────────────
# ENDPOINT: Telegram Alert (High-Conviction Signal Push)
# ─────────────────────────────────────────────────────────────
class TelegramConfig(BaseModel):
    bot_token: str
    chat_id: str

TELEGRAM_RUNTIME_CONFIG = {
    "token": os.getenv("TELEGRAM_BOT_TOKEN", ""),
    "chat_id": os.getenv("TELEGRAM_CHAT_ID", "")
}

@app.post("/api/telegram/config")
def set_telegram_config(cfg: TelegramConfig):
    global TELEGRAM_RUNTIME_CONFIG
    TELEGRAM_RUNTIME_CONFIG["token"] = cfg.bot_token
    TELEGRAM_RUNTIME_CONFIG["chat_id"] = cfg.chat_id
    return {"status": "Telegram config saved"}

@app.post("/api/telegram/test")
def test_telegram():
    import requests as req
    token = TELEGRAM_RUNTIME_CONFIG.get("token")
    chat_id = TELEGRAM_RUNTIME_CONFIG.get("chat_id")
    if not token or not chat_id:
        return {"error": "Telegram not configured. Please save your Bot Token and Chat ID first."}
    try:
        msg = "MyHalalTrade Test Alert! Your Telegram alerts are working correctly."
        r = req.post(f"https://api.telegram.org/bot{token}/sendMessage",
                     json={"chat_id": chat_id, "text": msg}, timeout=10)
        if r.status_code == 200:
            return {"status": "Message sent successfully!"}
        return {"error": r.json()}
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/telegram/send_signal")
def send_signal_alert(ticker: str, signal: str, conviction: int, price: float):
    import requests as req
    token = TELEGRAM_RUNTIME_CONFIG.get("token")
    chat_id = TELEGRAM_RUNTIME_CONFIG.get("chat_id")
    if not token or not chat_id:
        return {"error": "Telegram not configured"}
    icon = "STRONG BUY" == signal and "🚀🚀" or ("BUY" in signal and "📈" or "⚠️")
    msg = (
        f"{icon} MyHalalTrade SIGNAL ALERT\n\n"
        f"Asset: {ticker}\n"
        f"Signal: {signal}\n"
        f"Conviction: {conviction}%\n"
        f"Current Price: ${price:.2f}\n\n"
        f"Log in to MyHalalTrade to review."
    )
    try:
        r = req.post(f"https://api.telegram.org/bot{token}/sendMessage",
                     json={"chat_id": chat_id, "text": msg}, timeout=10)
        return {"status": "sent" if r.status_code == 200 else "failed"}
    except Exception as e:
        return {"error": str(e)}
# ─────────────────────────────────────────────────────────────
# ENDPOINT: Alpaca Config
# ─────────────────────────────────────────────────────────────
class AlpacaConfig(BaseModel):
    api_key: str
    secret_key: str

@app.post("/api/alpaca/config")
def save_alpaca_config(config: AlpacaConfig):
    from dotenv import set_key
    env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    set_key(env_file, "ALPACA_API_KEY", config.api_key)
    set_key(env_file, "ALPACA_SECRET_KEY", config.secret_key)
    return {"status": "success"}

# ─────────────────────────────────────────────────────────────
# ENDPOINT: Kelly Criterion Position Sizer
# ─────────────────────────────────────────────────────────────
@app.get("/api/kelly")
def kelly_criterion(ticker: str, equity: float = 10000.0, conviction: float = 60.0):
    """
    Kelly Criterion: f* = (bp - q) / b
    b = odds of winning (reward/risk ratio)
    p = probability of win (conviction score / 100)
    q = probability of loss (1 - p)
    Returns recommended position size in $ and shares.
    """
    try:
        t = yf.Ticker(ticker.upper())
        hist = t.history(period="1y")
        if hist.empty:
            return {"error": "No price data"}

        close = hist["Close"].values.astype(float)
        returns = np.diff(close) / close[:-1]
        sigma = float(np.std(returns))
        price = float(close[-1])

        p = conviction / 100.0  # Probability of win from AI conviction
        q = 1 - p
        # Use 2:1 reward/risk ratio (typical swing trade)
        tp_pct = sigma * 3
        sl_pct = sigma * 1.5
        b = tp_pct / sl_pct if sl_pct > 0 else 2.0

        kelly_fraction = (b * p - q) / b
        # Cap at 25% of portfolio (Half-Kelly for safety)
        half_kelly = max(0.0, min(kelly_fraction * 0.5, 0.25))

        recommended_dollars = round(equity * half_kelly, 2)
        recommended_shares = int(recommended_dollars / price) if price > 0 else 0
        risk_dollars = round(recommended_dollars * sl_pct, 2)
        target_dollars = round(recommended_dollars * tp_pct, 2)

        return {
            "ticker": ticker.upper(),
            "current_price": round(price, 2),
            "kelly_fraction": round(kelly_fraction, 4),
            "half_kelly_fraction": round(half_kelly, 4),
            "recommended_allocation_pct": round(half_kelly * 100, 1),
            "recommended_dollars": recommended_dollars,
            "recommended_shares": recommended_shares,
            "stop_loss_pct": round(sl_pct * 100, 2),
            "take_profit_pct": round(tp_pct * 100, 2),
            "max_loss_dollars": risk_dollars,
            "target_gain_dollars": target_dollars,
            "reward_risk_ratio": round(b, 2),
        }
    except Exception as e:
        return {"error": str(e)}

# ─────────────────────────────────────────────────────────────
# ENDPOINT: Earnings Calendar
# ─────────────────────────────────────────────────────────────
EARNINGS_CACHE = {"data": None, "timestamp": 0}

@app.get("/api/earnings")
def get_earnings_calendar():
    global EARNINGS_CACHE
    if time.time() - EARNINGS_CACHE["timestamp"] < 3600 and EARNINGS_CACHE["data"] is not None:
        return EARNINGS_CACHE["data"]

    # Only check stocks (not crypto/ETFs)
    stock_tickers = [t for t in WATCHLIST if "-USD" not in t and t not in ["GLD", "SLV", "SPUS", "HLAL", "UMMA", "SPSK"]]

    def fetch_earnings(ticker):
        try:
            t = yf.Ticker(ticker)
            cal = t.calendar
            info = t.fast_info
            price = float(getattr(info, 'last_price', 0) or 0)

            # cal is a dict with 'Earnings Date' key
            if cal is not None and 'Earnings Date' in cal:
                dates = cal['Earnings Date']
                if hasattr(dates, '__iter__') and not isinstance(dates, str):
                    dates = list(dates)
                    if dates:
                        next_date = str(dates[0].date()) if hasattr(dates[0], 'date') else str(dates[0])
                        return {"ticker": ticker, "next_earnings": next_date, "price": round(price, 2)}
            return None
        except:
            return None

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        raw = list(executor.map(fetch_earnings, stock_tickers[:20]))  # Limit to 20
    results = [r for r in raw if r is not None]
    results.sort(key=lambda x: x["next_earnings"])

    data = {"earnings": results, "count": len(results)}
    EARNINGS_CACHE["data"] = data
    EARNINGS_CACHE["timestamp"] = time.time()
    return data

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("api_server:app", host="0.0.0.0", port=port, reload=True)
