from typing import Dict, Any
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.config import RISK_TIERS

class RiskGate:
    def __init__(self, current_balance: float = 10000.0, max_daily_loss: float = -0.05):
        self.current_balance = current_balance
        self.max_daily_loss_amount = current_balance * max_daily_loss
        self.daily_pnl = 0.0
        
    def check_trade(self, tier: str, asset_class: str, order_type: str, price: float, qty: float) -> bool:
        """
        Validates a trade against the risk rules.
        """
        if self.daily_pnl <= self.max_daily_loss_amount:
            print(f"RISK GATE: Daily loss limit reached ({self.daily_pnl}). Halting trading.")
            return False
            
        tier_config = RISK_TIERS.get(tier)
        if not tier_config:
            print(f"RISK GATE: Unknown tier {tier}.")
            return False
            
        trade_value = price * qty
        max_investment = self.current_balance * tier_config['max_position_size']
        
        if order_type == 'BUY' and trade_value > max_investment:
            print(f"RISK GATE: Position size {trade_value} exceeds max allowed {max_investment} for tier {tier}.")
            return False
            
        # T+2 Settlement Rule for Stocks (Simplified MVP check)
        # In a real system, we would query the database to check when the stock was bought.
        # For now, we allow the signal to pass, but the paper broker will enforce it if needed.
        
        return True
