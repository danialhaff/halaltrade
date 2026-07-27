import backtrader as bt
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.config import RISK_TIERS

class BaseStrategy(bt.Strategy):
    """
    Base strategy class that handles risk limits and order tracking.
    """
    params = (
        ('tier', 'Medium'), # Low, Medium, High
    )
    
    def __init__(self):
        self.order = None
        self.buyprice = None
        self.buycomm = None
        
        tier_config = RISK_TIERS.get(self.p.tier)
        if tier_config:
            self.max_drawdown = tier_config['max_drawdown']
            self.max_position_size = tier_config['max_position_size']
        else:
            self.max_drawdown = -0.10
            self.max_position_size = 0.05
            
    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'BUY EXECUTED, Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Comm {order.executed.comm:.2f}')
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            elif order.issell():
                self.log(f'SELL EXECUTED, Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Comm {order.executed.comm:.2f}')
            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        self.order = None
        
    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.log(f'OPERATION PROFIT, GROSS {trade.pnl:.2f}, NET {trade.pnlcomm:.2f}')
        
    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()}, {txt}')
        
    def get_position_size(self):
        """Calculates how many shares to buy based on max_position_size limit."""
        cash = self.broker.get_cash()
        price = self.datas[0].close[0]
        max_investment = cash * self.max_position_size
        return int(max_investment / price)
