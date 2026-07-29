import time
import requests
import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from core.config import is_live_trading_enabled
from execution.alpaca_broker import AlpacaBroker
from execution.luno_broker import LunoBroker

API_URL = "http://localhost:8000/api"

# Keep track of active positions so we don't buy the same asset repeatedly
ACTIVE_POSITIONS = set()

def run_auto_bot():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting 24/7 Shariah Hedge Fund Bot...")
    if is_live_trading_enabled():
        print("CRITICAL WARNING: LIVE TRADING MODE IS ENABLED!")
        print("Bot is armed with REAL MONEY.")
    else:
        print("Mode: PAPER TRADING (Safe Mode)")

    stock_broker = AlpacaBroker()
    crypto_broker = LunoBroker()

    while True:
        try:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Scanning market for Alpha signals...")
            
            # 1. Fetch AI Signals
            res = requests.get(f"{API_URL}/signals")
            if res.status_code != 200:
                print("Failed to fetch signals from backend. Retrying in 60s...")
                time.sleep(60)
                continue
                
            data = res.json()
            signals = data.get("signals", [])
            
            # Filter for high conviction buys
            actionable = [s for s in signals if s.get("signal") in ("STRONG BUY", "BUY") 
                          and s.get("conviction", 0) >= 75 
                          and s.get("is_compliant")]
                          
            print(f"Found {len(actionable)} high-conviction trade setups.")
            
            for s in actionable:
                ticker = s["ticker"]
                if ticker in ACTIVE_POSITIONS:
                    continue # Already holding
                    
                print(f"-> Processing Auto-Trade: {ticker} (Conviction: {s['conviction']}%)")
                
                # 2. Get Kelly Position Sizing
                k_res = requests.get(f"{API_URL}/kelly?ticker={ticker}&equity=10000.0&conviction={s['conviction']}")
                if k_res.status_code != 200 or "error" in k_res.json():
                    print(f"   Skip: Failed to calculate position size for {ticker}")
                    continue
                    
                k_data = k_res.json()
                qty = k_data.get("recommended_shares", 0)
                price = k_data.get("current_price", 0.0)
                
                if qty <= 0:
                    print(f"   Skip: Kelly allocation says 0 shares for {ticker}")
                    continue
                    
                # 3. Execute Trade
                is_crypto = "-USD" in ticker
                broker = crypto_broker if is_crypto else stock_broker
                
                print(f"   Submitting order to {'Luno' if is_crypto else 'Alpaca'}: BUY {qty} {ticker}")
                order = broker.submit_order(ticker, "BUY", qty, "market")
                
                if order.get("status") == "accepted":
                    # 4. Log to P&L Journal
                    journal_payload = {
                        "ticker": ticker,
                        "action": "BUY",
                        "price": price,
                        "quantity": qty,
                        "conviction": s["conviction"],
                        "signal": s["signal"],
                        "notes": f"Auto-Execution (Kelly: {k_data.get('recommended_allocation_pct')}%)"
                    }
                    requests.post(f"{API_URL}/journal/trade", json=journal_payload)
                    print(f"   ✅ Trade Executed & Logged successfully.")
                    ACTIVE_POSITIONS.add(ticker)
                else:
                    print(f"   ❌ Broker rejected order for {ticker}: {order}")
                    
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Scan complete. Sleeping for 5 minutes...")
            time.sleep(300) # Sleep for 5 minutes
            
        except Exception as e:
            print(f"Bot encountered an error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    run_auto_bot()
