from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.audit_logger import Base, Session, engine

class PaperTrade(Base):
    __tablename__ = 'paper_trades'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    ticker = Column(String(50), nullable=False)
    action = Column(String(10), nullable=False) # 'BUY' or 'SELL'
    price = Column(Float, nullable=False)
    quantity = Column(Float, nullable=False)
    tier = Column(String(20), nullable=False)
    reasoning = Column(String(200), nullable=False)
    
# Create table if it doesn't exist
Base.metadata.create_all(engine)

class PaperBroker:
    def __init__(self):
        pass
        
    def execute_trade(self, ticker: str, action: str, price: float, qty: float, tier: str, reasoning: str):
        """
        Executes a paper trade by logging it to the database.
        """
        session = Session()
        try:
            trade = PaperTrade(
                ticker=ticker,
                action=action,
                price=price,
                quantity=qty,
                tier=tier,
                reasoning=reasoning
            )
            session.add(trade)
            session.commit()
            print(f"✅ PAPER BROKER EXECUTED: {action} {qty:.4f} {ticker} at ${price:.2f}")
        except Exception as e:
            session.rollback()
            print(f"❌ PAPER BROKER FAILED: {e}")
        finally:
            session.close()
