import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.config import LUNO_API_KEY, LUNO_SECRET_KEY
from execution.broker_interface import BrokerInterface

class LunoBroker(BrokerInterface):
    def __init__(self):
        self.api_key = LUNO_API_KEY
        self.secret_key = LUNO_SECRET_KEY
        self.base_url = "https://api.luno.com/api/1"
            
    def submit_order(self, ticker: str, action: str, qty: float, order_type: str = "MARKET") -> dict:
        """
        Submits an order to Luno via REST API (Mocked for safety).
        Luno requires pair IDs like XBTMYR instead of BTC-USD.
        """
        # Simple translation for MVP
        pair = "XBTMYR" if "BTC" in ticker else "ETHMYR"
        
        print(f"\n[LUNO API] -> POST {self.base_url}/marketorder")
        
        # The exact payload Luno expects for Market orders
        payload = {
            "pair": pair,
            "type": action.upper(),
            "base_volume": str(qty)
        }
        print(f"[LUNO API] Payload: {payload}")
        
        if self.api_key == "dummy_luno_key":
            print("[LUNO API] Error: API keys not configured.")
            return {"status": "failed", "reason": "No API keys"}
            
        # Mock successful response
        print(f"[LUNO API] ✅ Order Submitted to Broker: {action} {qty} {pair}")
        return {"status": "accepted", "id": "luno_mock_id_456"}

    def get_balance(self) -> float:
        return 10000.0
