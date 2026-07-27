from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import os
import sys

# Add parent directory to path so we can import from core
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.config import DB_URL

Base = declarative_base()

class ShariahScreeningLog(Base):
    __tablename__ = 'shariah_screening_logs'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    ticker = Column(String(50), nullable=False)
    asset_class = Column(String(20), nullable=False) # 'stock' or 'crypto'
    is_compliant = Column(Boolean, nullable=False)
    
    # Financial Ratios (for stocks)
    debt_to_mcap = Column(Float, nullable=True)
    cash_to_mcap = Column(Float, nullable=True)
    receivables_to_mcap = Column(Float, nullable=True)
    
    # Reason for failure or acceptance
    reasoning = Column(String(500), nullable=False)

# Setup Database Connection
engine = create_engine(DB_URL, echo=False)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

def log_screening_result(ticker: str, asset_class: str, is_compliant: bool, reasoning: str,
                         debt_to_mcap: float = None, cash_to_mcap: float = None, 
                         receivables_to_mcap: float = None):
    """
    Logs the result of a Shariah screening evaluation.
    This provides the mandatory audit trail.
    """
    session = Session()
    try:
        log_entry = ShariahScreeningLog(
            ticker=ticker,
            asset_class=asset_class,
            is_compliant=is_compliant,
            reasoning=reasoning,
            debt_to_mcap=debt_to_mcap,
            cash_to_mcap=cash_to_mcap,
            receivables_to_mcap=receivables_to_mcap
        )
        session.add(log_entry)
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Failed to log audit entry for {ticker}: {e}")
    finally:
        session.close()

def get_recent_logs(limit=10):
    session = Session()
    try:
        return session.query(ShariahScreeningLog).order_by(ShariahScreeningLog.timestamp.desc()).limit(limit).all()
    finally:
        session.close()
