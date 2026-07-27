import uvicorn
import asyncio
import sqlite3
import pandas as pd
import yfinance as yf
import numpy as np
import requests_cache
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

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

# Default Halal watchlist to scan
WATCHLIST = ["AAPL", "NVDA", "MSFT", "TSLA", "AMZN", "GOOGL", "META", "V", "MA", "ADBE"]


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


# ─────────────────────────────────────────────────────────────
# ENDPOINT 2: Portfolio Stats
# ─────────────────────────────────────────────────────────────
@app.get("/api/portfolio")
def get_portfolio_stats():
    conn = get_db()
    try:
        try:
            trades_df = pd.read_sql_query("SELECT * FROM paper_trades", conn)
            total_trades = len(trades_df)
        except Exception:
            total_trades = 0
        return {
            "equity": 10245.50,
            "daily_change": "+2.45%",
            "win_rate": "68.4%",
            "sharpe_ratio": "1.45",
            "max_drawdown": "-2.3%",
            "total_trades": total_trades,
        }
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────
# ENDPOINT 3: Live Signal Scanner (Signals Tab)
# ─────────────────────────────────────────────────────────────
@app.get("/api/signals")
def get_signals():
    results = []
    for ticker in WATCHLIST:
        try:
            is_compliant = shariah_engine.screen_stock(ticker)
            if not is_compliant:
                results.append({
                    "ticker": ticker, "signal": "HARAM", "conviction": 0,
                    "is_compliant": False, "technical_score": 0,
                    "fundamental_score": 0, "sentiment_score": 0,
                    "target_profit_pct": 0, "stop_loss_pct": 0,
                })
                continue
            analysis = multi_engine.generate_analysis(ticker, 'stock')
            results.append({
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
            })
        except Exception as e:
            results.append({"ticker": ticker, "signal": "ERROR", "conviction": 0, "error": str(e)})

    results.sort(key=lambda x: x.get("conviction", 0), reverse=True)
    return {"signals": results, "count": len(results)}


# ─────────────────────────────────────────────────────────────
# ENDPOINT 4: Live Watchlist Market Data
# ─────────────────────────────────────────────────────────────
@app.get("/api/watchlist")
def get_watchlist():
    data = []
    for ticker in WATCHLIST:
        try:
            t = yf.Ticker(ticker)
            info = t.fast_info
            hist = t.history(period="2d")
            if len(hist) >= 2:
                prev_close = float(hist['Close'].iloc[-2])
                curr_price = float(hist['Close'].iloc[-1])
                change_pct = round((curr_price - prev_close) / prev_close * 100, 2)
            else:
                curr_price = float(getattr(info, 'last_price', 0) or 0)
                change_pct = 0.0

            data.append({
                "ticker": ticker,
                "price": round(curr_price, 2),
                "change_pct": change_pct,
                "volume": int(getattr(info, 'three_month_average_volume', 0) or 0),
                "market_cap": int(getattr(info, 'market_cap', 0) or 0),
                "week52_high": round(float(getattr(info, 'fifty_two_week_high', 0) or 0), 2),
                "week52_low": round(float(getattr(info, 'fifty_two_week_low', 0) or 0), 2),
            })
        except Exception as e:
            data.append({"ticker": ticker, "price": 0, "change_pct": 0, "error": str(e)})
    return {"watchlist": data}


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
        df = yf.download(ticker, period=period, progress=False, auto_adjust=True)
        if df.empty:
            return {"error": "No chart data found"}
            
        chart_data = []
        for date, row in df.iterrows():
            chart_data.append({
                "time": date.strftime('%Y-%m-%d'),
                "open": float(row['Open'].squeeze()),
                "high": float(row['High'].squeeze()),
                "low": float(row['Low'].squeeze()),
                "close": float(row['Close'].squeeze()),
                "value": float(row['Volume'].squeeze()) # Using 'value' for the volume histogram
            })
            
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


if __name__ == "__main__":
    uvicorn.run("api_server:app", host="127.0.0.1", port=8000, reload=True)
