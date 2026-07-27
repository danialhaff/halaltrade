import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from backtest.engine import run_backtest
from backtest.reporter import print_report
from strategy.swing_strategy import SwingStrategy
from strategy.intraday_strategy import IntradayStrategy

def main():
    print("Starting Phase 2 Backtest Suite...")

    # Test 1: Apple (Compliant Stock) using Swing Strategy
    # Data from 2021-01-01 to 2024-01-01 (3 years)
    strat_aapl = run_backtest(
        ticker="AAPL",
        start_date="2021-01-01",
        end_date="2024-01-01",
        strategy_class=SwingStrategy,
        asset_class="stock",
        initial_cash=10000.0
    )
    print_report(strat_aapl)
    
    # Test 2: Maybank (Non-Compliant Stock)
    strat_maybank = run_backtest(
        ticker="1155.KL",
        start_date="2021-01-01",
        end_date="2024-01-01",
        strategy_class=SwingStrategy,
        asset_class="stock",
        initial_cash=10000.0
    )
    # This should abort before backtesting, strat_maybank will be None
    print_report(strat_maybank)

    # Test 3: Bitcoin (Compliant Crypto) using Intraday Strategy (MACD)
    strat_btc = run_backtest(
        ticker="BTC-USD",
        start_date="2022-01-01",
        end_date="2024-01-01", # 2 years of daily for demo
        strategy_class=IntradayStrategy,
        asset_class="crypto",
        initial_cash=10000.0
    )
    print_report(strat_btc)

if __name__ == "__main__":
    main()
