import time
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from core.config import is_live_trading_enabled, AUTO_APPROVED_TIERS
from screener.shariah_engine import ShariahEngine
from data.yfinance_provider import YFinanceProvider
from risk.risk_gate import RiskGate
from execution.telegram_bot import TelegramNotifier
from execution.paper_broker import PaperBroker
from execution.alpaca_broker import AlpacaBroker
from execution.luno_broker import LunoBroker

from strategy.multi_factor_engine import MultiFactorEngine

def run_semi_auto_bot():
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Starting Shariah Trading Bot...")
    if is_live_trading_enabled():
        print("CRITICAL WARNING: LIVE TRADING MODE IS ENABLED!")
        print("Exiting immediately. Safety default requires manual override in code for first execution.")
        return
    else:
        print("Mode: PAPER TRADING (Safe Mode)")

    provider = YFinanceProvider()
    shariah_engine = ShariahEngine(provider)
    multi_factor = MultiFactorEngine(provider)
    risk_gate = RiskGate(current_balance=10000.0)
    telegram = TelegramNotifier()
    broker = PaperBroker()

    # MOCK SIGNALS from Layer 3 (In a real scenario, this is output from the Strategy Engine scanning live data)
    signals = [
        {"ticker": "AAPL", "action": "BUY", "price": 185.50, "tier": "Low", "asset_class": "stock", "reason": "Swing Dual MA Golden Cross"},
        {"ticker": "JPM", "action": "BUY", "price": 145.20, "tier": "Low", "asset_class": "stock", "reason": "Swing MA Cross (Should Fail Shariah)"},
        {"ticker": "BTC-USD", "action": "BUY", "price": 42000.00, "tier": "High", "asset_class": "crypto", "reason": "Intraday MACD Momentum"}
    ]

    for signal in signals:
        ticker = signal["ticker"]
        action = signal["action"]
        price = signal["price"]
        tier = signal["tier"]
        asset_class = signal["asset_class"]
        
        print(f"\n--- Processing Signal: {action} {ticker} ---")
        
        # 1. Shariah Screen
        if asset_class == 'stock':
            is_compliant = shariah_engine.screen_stock(ticker)
        else:
            is_compliant = shariah_engine.screen_crypto(ticker)
            
        if not is_compliant:
            print(f"-> ABORTED: {ticker} failed Shariah screening.")
            continue
            
        # 2. Multi-Factor Analysis (NEW PHASE 6)
        print(f"-> Running Multi-Factor Analysis for {ticker}...")
        analysis = multi_factor.generate_analysis(ticker, asset_class)
        
        if analysis['conviction'] < 60:
            print(f"-> ABORTED: Conviction score too low ({analysis['conviction']}%).")
            continue
            
        # 3. Position Sizing
        # Determine quantity based on risk tier and current price
        tier_config = {"Low": 0.05, "Medium": 0.10, "High": 0.20} # simple mock config lookup
        target_allocation = 10000.0 * tier_config.get(tier, 0.05)
        qty = target_allocation / price
        
        # 4. Risk Gate
        passed_risk = risk_gate.check_trade(tier, asset_class, action, price, qty)
        if not passed_risk:
            print(f"-> ABORTED: {ticker} failed Risk Gate.")
            continue
            
        # 5. Check Fully-Auto vs Semi-Auto
        if tier in AUTO_APPROVED_TIERS:
            print(f"-> Fully-Auto bypass active for Tier {tier}. Routing directly to Live Broker API...")
            
            # Select Broker based on Asset Class
            if asset_class == 'stock':
                live_broker = AlpacaBroker()
            else:
                live_broker = LunoBroker()
                
            # Submit Live/Paper Order to API
            api_result = live_broker.submit_order(ticker, action, qty)
            if api_result['status'] == 'accepted':
                # Log to our internal paper database for tracking as well
                broker.execute_trade(ticker, action, price, qty, tier, f"Fully-Auto ({analysis['signal']}): {analysis['conviction']}% Conviction")
            
        else:
            # 6. Telegram Notification (Layer 5) for Semi-Auto
            print(f"-> Signal verified. Requesting approval via Telegram...")
            telegram.send_signal_sync(ticker, action, price, qty, tier, analysis)
            
            user_input = input(f"\n[SEMI-AUTO PROMPT] Awaiting approval for {ticker}. Type 'APPROVE {ticker}' to execute: ")
            
            if user_input.strip() == f"APPROVE {ticker}":
                broker.execute_trade(ticker, action, price, qty, tier, f"Semi-Auto ({analysis['signal']}): {analysis['conviction']}% Conviction")
            else:
                print(f"-> User rejected trade for {ticker}. Skipping.")
            
    print("\nBot run completed.")

if __name__ == "__main__":
    run_semi_auto_bot()
