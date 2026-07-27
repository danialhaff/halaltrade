import backtrader as bt
import yfinance as yf
import pandas as pd
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from screener.shariah_engine import ShariahEngine
from data.yfinance_provider import YFinanceProvider
from strategy.swing_strategy import SwingStrategy

def run_backtest(ticker: str, start_date: str, end_date: str, strategy_class, asset_class: str, initial_cash=10000.0):
    print(f"\n{'='*50}")
    print(f"BACKTESTING: {ticker} ({start_date} to {end_date})")
    print(f"{'='*50}")

    # 1. Shariah Screening First!
    print(f"Step 1: Running Shariah Compliance Screen...")
    provider = YFinanceProvider()
    engine = ShariahEngine(provider)
    
    if asset_class == 'stock':
        is_compliant = engine.screen_stock(ticker)
    else:
        is_compliant = engine.screen_crypto(ticker)
        
    if not is_compliant:
        print(f"FAILED: {ticker} failed Shariah screening. We cannot trade this asset.")
        return None

    print(f"PASSED: {ticker} is Shariah-compliant. Proceeding to backtest.")

    # 2. Fetch Historical Data
    print(f"Step 2: Fetching historical data from yFinance...")
    df = yf.download(ticker, start=start_date, end=end_date, progress=False)
    
    # yfinance sometimes returns multi-index columns for single tickers in newer versions
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(1)
        
    if df.empty:
        print("❌ Error: No data fetched.")
        return None
        
    # 3. Setup Backtrader Engine
    print(f"Step 3: Running Strategy Engine...")
    cerebro = bt.Cerebro()
    
    # Add strategy
    cerebro.addstrategy(strategy_class)
    
    # Create data feed
    data = bt.feeds.PandasData(dataname=df)
    cerebro.adddata(data)
    
    # Set starting cash
    cerebro.broker.setcash(initial_cash)
    
    # Set commission (e.g., 0.1%)
    cerebro.broker.setcommission(commission=0.001)
    
    # Add Analyzers
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')

    start_value = cerebro.broker.getvalue()
    print(f'Starting Portfolio Value: {start_value:.2f}')

    # Run
    results = cerebro.run()
    strat = results[0]

    end_value = cerebro.broker.getvalue()
    print(f'Final Portfolio Value: {end_value:.2f}')
    
    # 4. Return results for reporter
    return strat
