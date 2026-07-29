import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ---------------------------------------------------------------------
# NON-NEGOTIABLE SAFETY RULES
# ---------------------------------------------------------------------
# The system MUST start in "paper trading" mode by default.
LIVE_TRADING = os.getenv("LIVE_TRADING", "false").lower() == "true"

# Risk Tier Limits
RISK_TIERS = {
    "Low": {
        "max_drawdown": -0.08,
        "max_position_size": 0.05,
    },
    "Medium": {
        "max_drawdown": -0.20,
        "max_position_size": 0.10,
    },
    "High": {
        "max_drawdown": -0.40,
        "max_position_size": 0.20,
    }
}

# Crypto whitelist (manual only)
# BTC and ETH are standard, but this list MUST be manually managed
CRYPTO_WHITELIST = [
    "BTC",
    "ETH",
]

# ETF and Commodity Whitelist (Islamic Indices & Precious Metals)
ETF_WHITELIST = [
    "SPUS",  # SP Funds S&P 500 Sharia Industry Exclusions ETF
    "HLAL",  # Wahed FTSE USA Shariah ETF
    "UMMA",  # Wahed Dow Jones Islamic World ETF
    "SPSK",  # SP Funds Dow Jones Global Sukuk ETF
    "GLD",   # SPDR Gold Trust (Commodity)
    "SLV",   # iShares Silver Trust (Commodity)
]

# Database Config
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "shariah_audit.db")
DB_URL = os.getenv("DB_URL", f"sqlite:///{DB_PATH}")

def is_live_trading_enabled() -> bool:
    """Returns True if live trading is explicitly enabled via env var."""
    return LIVE_TRADING

# Telegram Config
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Fully-Auto Config
# Tiers in this list will bypass Telegram approval and execute directly
AUTO_APPROVED_TIERS = ["Low"]

# Broker API Keys
ALPACA_API_KEY = os.getenv("ALPACA_API_KEY", "dummy_alpaca_key")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY", "dummy_alpaca_secret")
ALPACA_BASE_URL = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")

LUNO_API_KEY = os.getenv("LUNO_API_KEY", "dummy_luno_key")
LUNO_SECRET_KEY = os.getenv("LUNO_SECRET_KEY", "dummy_luno_secret")
