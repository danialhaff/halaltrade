from abc import ABC, abstractmethod

class BrokerInterface(ABC):
    """
    Abstract interface for executing live/paper trades via an API.
    """
    
    @abstractmethod
    def submit_order(self, ticker: str, action: str, qty: float, order_type: str = "market") -> dict:
        """
        Submits an order to the broker.
        Returns a dictionary with the order details and status.
        """
        pass
        
    @abstractmethod
    def get_balance(self) -> float:
        """
        Returns the current available cash balance.
        """
        pass
