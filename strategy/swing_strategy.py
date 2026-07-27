import backtrader as bt
from .base_strategy import BaseStrategy

class SwingStrategy(BaseStrategy):
    """
    Swing Trading Strategy using Dual Moving Average Crossover and RSI filter.
    Allowed for Low, Medium, and High Risk tiers.
    """
    params = (
        ('fast_ma', 50),
        ('slow_ma', 200),
        ('rsi_period', 14),
        ('rsi_overbought', 70),
    )

    def __init__(self):
        super().__init__()
        
        # Indicators
        self.fast_sma = bt.indicators.SimpleMovingAverage(
            self.datas[0], period=self.p.fast_ma)
        self.slow_sma = bt.indicators.SimpleMovingAverage(
            self.datas[0], period=self.p.slow_ma)
        self.rsi = bt.indicators.RelativeStrengthIndex(
            self.datas[0], period=self.p.rsi_period)
            
        # Crossover signal (1.0 = Fast crosses above Slow, -1.0 = Fast crosses below Slow)
        self.crossover = bt.indicators.CrossOver(self.fast_sma, self.slow_sma)

    def next(self):
        # Simply log the closing price of the series from the reference
        # self.log(f'Close, {self.datas[0].close[0]:.2f}')

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        # Check if we are in the market
        if not self.position:
            # Not yet ... we MIGHT BUY if ...
            # 1. Fast MA crosses above Slow MA (Golden Cross)
            # 2. RSI is not overbought (< 70)
            if self.crossover > 0 and self.rsi[0] < self.p.rsi_overbought:
                self.log('BUY CREATE')
                size = self.get_position_size()
                if size > 0:
                    self.order = self.buy(size=size)
        else:
            # Already in the market ... we might sell if ...
            # Fast MA crosses below Slow MA (Death Cross)
            if self.crossover < 0:
                self.log('SELL CREATE')
                self.order = self.sell(size=self.position.size)
