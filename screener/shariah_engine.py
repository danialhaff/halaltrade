import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.config import CRYPTO_WHITELIST
from db.audit_logger import log_screening_result
from data.provider_interface import DataProvider

# AAOIFI Thresholds
MAX_DEBT_RATIO = 0.33
MAX_CASH_RATIO = 0.33
MAX_RECEIVABLES_RATIO = 0.49

# Non-compliant business keywords (simplified for MVP)
NON_COMPLIANT_KEYWORDS = [
    "alcohol", "gambling", "tobacco", "weapon", "defense", 
    "bank", "insurance", "pork", "casino", "brewery"
]

class ShariahEngine:
    def __init__(self, data_provider: DataProvider):
        self.provider = data_provider

    def screen_crypto(self, symbol: str) -> bool:
        """
        Screens a crypto asset. ONLY manual whitelist is allowed.
        """
        base_symbol = symbol.split('-')[0].upper()
        is_compliant = base_symbol in [c.upper() for c in CRYPTO_WHITELIST]
        reason = "Pass: In manual whitelist" if is_compliant else f"Fail: {symbol} not in manual whitelist"
        
        log_screening_result(
            ticker=symbol,
            asset_class='crypto',
            is_compliant=is_compliant,
            reasoning=reason
        )
        return is_compliant

    def screen_stock(self, ticker: str) -> bool:
        """
        Screens a stock using AAOIFI financial ratio screens and business activity screens.
        """
        # 1. Business Activity Screen
        info = self.provider.get_company_info(ticker)
        
        # Check industry/sector and summary against keywords
        text_to_check = f"{info.get('industry', '')} {info.get('sector', '')} {info.get('businessSummary', '')}".lower()
        
        for keyword in NON_COMPLIANT_KEYWORDS:
            if keyword in text_to_check:
                reason = f"Fail: Business activity screen failed on keyword '{keyword}'"
                log_screening_result(ticker, 'stock', False, reason)
                return False
                
        # 2. Financial Ratios Screen (AAOIFI)
        ratios = self.provider.get_financial_ratios(ticker)
        
        debt = ratios.get('debt_to_mcap')
        cash = ratios.get('cash_to_mcap')
        receivables = ratios.get('receivables_to_mcap')
        
        if debt is None or cash is None or receivables is None:
            reason = "Fail: Missing financial data to calculate AAOIFI ratios"
            log_screening_result(ticker, 'stock', False, reason, debt, cash, receivables)
            return False
            
        if debt >= MAX_DEBT_RATIO:
            reason = f"Fail: Debt ratio {debt:.2%} >= {MAX_DEBT_RATIO:.0%}"
            log_screening_result(ticker, 'stock', False, reason, debt, cash, receivables)
            return False
            
        if cash >= MAX_CASH_RATIO:
            reason = f"Fail: Cash ratio {cash:.2%} >= {MAX_CASH_RATIO:.0%}"
            log_screening_result(ticker, 'stock', False, reason, debt, cash, receivables)
            return False
            
        if receivables >= MAX_RECEIVABLES_RATIO:
            reason = f"Fail: Receivables ratio {receivables:.2%} >= {MAX_RECEIVABLES_RATIO:.0%}"
            log_screening_result(ticker, 'stock', False, reason, debt, cash, receivables)
            return False
            
        # If all checks pass
        reason = "Pass: All AAOIFI criteria met"
        log_screening_result(ticker, 'stock', True, reason, debt, cash, receivables)
        return True
