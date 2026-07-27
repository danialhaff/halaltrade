import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from screener.shariah_engine import ShariahEngine
from data.yfinance_provider import YFinanceProvider
from db.audit_logger import get_recent_logs

def run_demo():
    print("=" * 60)
    print("SHARIAH-COMPLIANT MULTI-TIER TRADING SYSTEM - MVP DEMO")
    print("=" * 60)
    
    provider = YFinanceProvider()
    engine = ShariahEngine(provider)
    
    assets_to_test = [
        {"symbol": "AAPL", "type": "stock"},
        {"symbol": "BTC", "type": "crypto"},
        {"symbol": "JPM", "type": "stock"}, # JP Morgan (Should fail business screen)
        {"symbol": "DOGE", "type": "crypto"}, # Should fail crypto whitelist
        {"symbol": "1155.KL", "type": "stock"}, # Maybank (Should fail business screen, or ratio if missing)
        {"symbol": "5183.KL", "type": "stock"} # Petronas Chemicals
    ]
    
    print("\nRunning compliance checks...")
    for asset in assets_to_test:
        symbol = asset['symbol']
        asset_type = asset['type']
        
        print(f"Screening {symbol} ({asset_type})...")
        if asset_type == 'stock':
            is_compliant = engine.screen_stock(symbol)
        else:
            is_compliant = engine.screen_crypto(symbol)
            
        status = "PASS" if is_compliant else "FAIL"
        print(f" -> Result: {status}")
        
    print("\n" + "=" * 60)
    print("AUDIT TRAIL LOGS (from SQLite DB)")
    print("=" * 60)
    
    logs = get_recent_logs(10)
    for log in reversed(logs):
        status = "COMPLIANT" if log.is_compliant else "NON-COMPLIANT"
        print(f"[{log.timestamp}] {log.ticker} ({log.asset_class}): {status}")
        print(f"  Reason: {log.reasoning}")
        if log.asset_class == 'stock' and not log.is_compliant:
            print(f"  Ratios -> Debt: {log.debt_to_mcap}, Cash: {log.cash_to_mcap}, Receivables: {log.receivables_to_mcap}")
        print("-" * 40)

if __name__ == "__main__":
    run_demo()
