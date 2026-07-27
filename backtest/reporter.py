def print_report(strat):
    """
    Extracts analyzers from the strategy and prints a formatted report.
    """
    if strat is None:
        return
        
    print(f"\n{'='*50}")
    print("PERFORMANCE REPORT")
    print(f"{'='*50}")
    
    # Returns (CAGR)
    returns = strat.analyzers.returns.get_analysis()
    cagr = returns.get('cagr', 0)
    print(f"CAGR (Compound Annual Growth Rate): {cagr:.2%}")
    
    # Drawdown
    drawdown = strat.analyzers.drawdown.get_analysis()
    max_dd = drawdown.get('max', {}).get('drawdown', 0)
    print(f"Max Drawdown: -{max_dd:.2f}%")
    
    # Sharpe Ratio
    sharpe = strat.analyzers.sharpe.get_analysis()
    sharpe_ratio = sharpe.get('sharperatio', 0)
    if sharpe_ratio is None:
        sharpe_ratio = 0.0
    print(f"Sharpe Ratio: {sharpe_ratio:.2f}")
    
    # Trade Analysis (Win Rate, Risk:Reward)
    trades = strat.analyzers.trades.get_analysis()
    total_trades = trades.get('total', {}).get('closed', 0)
    
    if total_trades > 0:
        won_trades = trades.get('won', {}).get('total', 0)
        lost_trades = trades.get('lost', {}).get('total', 0)
        
        win_rate = won_trades / total_trades
        print(f"Win Rate: {win_rate:.2%} ({won_trades} Won / {total_trades} Closed)")
        
        avg_win = trades.get('won', {}).get('pnl', {}).get('average', 0)
        avg_loss = abs(trades.get('lost', {}).get('pnl', {}).get('average', 0))
        
        if avg_loss > 0:
            risk_reward = avg_win / avg_loss
            print(f"Risk:Reward Ratio: 1 : {risk_reward:.2f}")
        else:
            print("Risk:Reward Ratio: Infinite (No losing trades)")
    else:
        print("Total Closed Trades: 0")
        
    print(f"{'='*50}\n")
