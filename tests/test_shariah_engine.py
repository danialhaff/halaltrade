import sys
import os
import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from screener.shariah_engine import ShariahEngine
from data.provider_interface import DataProvider

class MockDataProvider(DataProvider):
    def __init__(self):
        self.mock_info = {}
        self.mock_ratios = {}
        
    def get_company_info(self, ticker: str):
        return self.mock_info.get(ticker, {"industry": "Tech", "sector": "Tech", "businessSummary": "Doing tech stuff"})
        
    def get_financial_ratios(self, ticker: str):
        # Default passing ratios
        return self.mock_ratios.get(ticker, {
            "debt_to_mcap": 0.10,
            "cash_to_mcap": 0.10,
            "receivables_to_mcap": 0.10
        })

@pytest.fixture
def engine():
    provider = MockDataProvider()
    return ShariahEngine(provider), provider

def test_crypto_whitelist(engine):
    shariah_engine, _ = engine
    # Based on config, BTC and ETH are whitelisted
    assert shariah_engine.screen_crypto("BTC") == True
    assert shariah_engine.screen_crypto("ETH") == True
    
    # Random coin should fail
    assert shariah_engine.screen_crypto("DOGE") == False
    
def test_stock_pass(engine):
    shariah_engine, _ = engine
    assert shariah_engine.screen_stock("AAPL") == True
    
def test_stock_fail_business(engine):
    shariah_engine, provider = engine
    provider.mock_info["BADSTOCK"] = {
        "industry": "Banks",
        "sector": "Financial",
        "businessSummary": "A conventional bank that deals with interest"
    }
    assert shariah_engine.screen_stock("BADSTOCK") == False

def test_stock_fail_debt_ratio(engine):
    shariah_engine, provider = engine
    provider.mock_ratios["HIGHDEBT"] = {
        "debt_to_mcap": 0.35, # Fails (>= 0.33)
        "cash_to_mcap": 0.10,
        "receivables_to_mcap": 0.10
    }
    assert shariah_engine.screen_stock("HIGHDEBT") == False
    
def test_stock_edge_case_debt_ratio(engine):
    shariah_engine, provider = engine
    provider.mock_ratios["EDGE_FAIL"] = {
        "debt_to_mcap": 0.33, # Fails exactly on threshold
        "cash_to_mcap": 0.10,
        "receivables_to_mcap": 0.10
    }
    assert shariah_engine.screen_stock("EDGE_FAIL") == False
    
    provider.mock_ratios["EDGE_PASS"] = {
        "debt_to_mcap": 0.3299, # Passes just below threshold
        "cash_to_mcap": 0.10,
        "receivables_to_mcap": 0.10
    }
    assert shariah_engine.screen_stock("EDGE_PASS") == True

def test_missing_data(engine):
    shariah_engine, provider = engine
    provider.mock_ratios["NODATA"] = {
        "debt_to_mcap": None, 
        "cash_to_mcap": None,
        "receivables_to_mcap": None
    }
    assert shariah_engine.screen_stock("NODATA") == False
