import backtrader as bt
from .base_strategy import BaseStrategy

class IntradayStrategy(BaseStrategy):
    """
    Intraday Strategy using MACD momentum.
    Allowed for Medium and High Risk tiers (primarily Crypto).
    """
    params = (
        ('macd1', 12),
        ('macd2', 26),
        ('macdsig', 9),
    )

    def __init__(self):
        super().__init__()
        
        # MACD Indicator
        self.macd = bt.indicators.MACD(
            self.datas[0],
            period_me1=self.p.macd1,
            period_me2=self.p.macd2,
            period_signal=self.p.macdsig
        )
        
        # Crossover signal (MACD line crosses Signal line)
        self.crossover = bt.indicators.CrossOver(self.macd.macd, self.macd.signal)

    def next(self):
        if self.order:
            return

        if not self.position:
            # Buy if MACD line crosses above Signal line
            if self.crossover > 0:
                self.log('BUY CREATE')
                size = self.get_position_size()
                if size > 0:
                    self.order = self.buy(size=size)
        else:
            # Sell if MACD line crosses below Signal line
            if self.crossover < 0:
                self.log('SELL CREATE')
                self.order = self.sell(size=self.position.size)
