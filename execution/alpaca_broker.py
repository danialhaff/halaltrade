import sys
import os
import requests
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from execution.broker_interface import BrokerInterface

class AlpacaBroker(BrokerInterface):
    def __init__(self):
        # Always reload dotenv so it picks up newly saved keys
        env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
        load_dotenv(env_file, override=True)
        
        self.api_key = os.getenv("ALPACA_API_KEY", "")
        self.secret_key = os.getenv("ALPACA_SECRET_KEY", "")
        self.base_url = "https://paper-api.alpaca.markets" # Hardcode to paper for safety
            
    def submit_order(self, ticker: str, action: str, qty: float, order_type: str = "market") -> dict:
        """
        Submits a LIVE paper order to Alpaca via REST API.
        """
        print(f"\n[ALPACA API] -> POST {self.base_url}/v2/orders")
        
        if not self.api_key or not self.secret_key:
            print("[ALPACA API] Error: API keys not configured. Trade blocked.")
            return {"status": "failed", "reason": "No API keys configured"}

        payload = {
            "symbol": ticker.upper(),
            "qty": qty,
            "side": action.lower(),
            "type": order_type,
            "time_in_force": "day"
        }
        
        headers = {
            "APCA-API-KEY-ID": self.api_key,
            "APCA-API-SECRET-KEY": self.secret_key,
            "accept": "application/json",
            "content-type": "application/json"
        }
        
        try:
            res = requests.post(f"{self.base_url}/v2/orders", json=payload, headers=headers, timeout=10)
            if res.status_code in [200, 201]:
                data = res.json()
                print(f"[ALPACA API] ✅ Order Accepted: {data['id']}")
                return {"status": "accepted", "id": data["id"]}
            else:
                print(f"[ALPACA API] ❌ Order Rejected: {res.text}")
                return {"status": "failed", "reason": res.text}
        except Exception as e:
            print(f"[ALPACA API] Exception: {e}")
            return {"status": "failed", "reason": str(e)}

    def get_balance(self) -> float:
        if not self.api_key:
            return 10000.0
        headers = {
            "APCA-API-KEY-ID": self.api_key,
            "APCA-API-SECRET-KEY": self.secret_key
        }
        try:
            res = requests.get(f"{self.base_url}/v2/account", headers=headers, timeout=10)
            if res.status_code == 200:
                return float(res.json().get('equity', 10000.0))
        except:
            pass
        return 10000.0
