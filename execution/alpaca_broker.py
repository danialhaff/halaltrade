import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.config import ALPACA_API_KEY, ALPACA_SECRET_KEY, ALPACA_BASE_URL, is_live_trading_enabled
from execution.broker_interface import BrokerInterface

class AlpacaBroker(BrokerInterface):
    def __init__(self):
        self.api_key = ALPACA_API_KEY
        self.secret_key = ALPACA_SECRET_KEY
        self.base_url = ALPACA_BASE_URL
        
        # Security Check
        if is_live_trading_enabled() and "paper" in self.base_url:
            print("WARNING: LIVE TRADING is enabled but Alpaca URL is set to PAPER.")
            
    def submit_order(self, ticker: str, action: str, qty: float, order_type: str = "market") -> dict:
        """
        Submits an order to Alpaca via REST API (Mocked for safety).
        """
        print(f"\n[ALPACA API] -> POST {self.base_url}/v2/orders")
        
        # The exact payload Alpaca expects
        payload = {
            "symbol": ticker,
            "qty": qty,
            "side": action.lower(),
            "type": order_type,
            "time_in_force": "day"
        }
        print(f"[ALPACA API] Payload: {payload}")
        
        if self.api_key == "dummy_alpaca_key":
            print("[ALPACA API] Error: API keys not configured.")
            return {"status": "failed", "reason": "No API keys"}
            
        # Mock successful response
        print(f"[ALPACA API] ✅ Order Submitted to Broker: {action} {qty} {ticker}")
        return {"status": "accepted", "id": "alpaca_mock_id_123"}

    def get_balance(self) -> float:
        return 10000.0
