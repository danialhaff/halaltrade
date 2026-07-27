from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class DataProvider(ABC):
    """
    Abstract base class for data providers.
    Allows swapping out yFinance for Alpha Vantage, FMP, etc., in the future.
    """
    
    @abstractmethod
    def get_company_info(self, ticker: str) -> Dict[str, Any]:
        """
        Fetch company metadata (industry, sector, description) for business screening.
        """
        pass

    @abstractmethod
    def get_financial_ratios(self, ticker: str) -> Dict[str, Optional[float]]:
        """
        Fetch financial metrics required for AAOIFI screening:
        - Total Debt
        - Cash and Short Term Investments
        - Total Receivables
        - Market Capitalization
        
        Returns a dictionary with 'debt_to_mcap', 'cash_to_mcap', 'receivables_to_mcap'
        """
        pass
