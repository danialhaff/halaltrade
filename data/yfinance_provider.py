import yfinance as yf
from typing import Dict, Any, Optional
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from provider_interface import DataProvider

class YFinanceProvider(DataProvider):
    
    def get_company_info(self, ticker: str) -> Dict[str, Any]:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            return {
                "industry": info.get("industry", "Unknown"),
                "sector": info.get("sector", "Unknown"),
                "businessSummary": info.get("longBusinessSummary", "")
            }
        except Exception as e:
            print(f"Error fetching company info for {ticker}: {e}")
            return {"industry": "Unknown", "sector": "Unknown", "businessSummary": ""}

    def get_financial_ratios(self, ticker: str) -> Dict[str, Optional[float]]:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Note: yfinance can sometimes be missing data for international stocks
            mcap = info.get('marketCap')
            if not mcap:
                return {"debt_to_mcap": None, "cash_to_mcap": None, "receivables_to_mcap": None}
                
            total_debt = info.get('totalDebt', 0)
            total_cash = info.get('totalCash', 0)
            
            # yfinance doesn't easily expose 'total receivables' in .info directly, 
            # we try to get it from the balance sheet if available.
            bs = stock.balance_sheet
            receivables = 0
            if 'Accounts Receivable' in bs.index and not bs.empty:
                # Get the most recent value
                receivables = bs.loc['Accounts Receivable'].iloc[0]
            
            if receivables is None or str(receivables) == 'nan':
                receivables = 0
                
            return {
                "debt_to_mcap": total_debt / mcap if mcap else None,
                "cash_to_mcap": total_cash / mcap if mcap else None,
                "receivables_to_mcap": receivables / mcap if mcap else None
            }
        except Exception as e:
            print(f"Error fetching financial ratios for {ticker}: {e}")
            return {"debt_to_mcap": None, "cash_to_mcap": None, "receivables_to_mcap": None}
