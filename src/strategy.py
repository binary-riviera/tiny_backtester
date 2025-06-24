from abc import ABC, abstractmethod
from backtester_types import Order, Datasets


class Strategy(ABC):
    tickers: set[str]
    funds: int = 10000

    @abstractmethod
    def preload(self, data: Datasets) -> None:
        """Calculate new columns on data"""
        pass

    @abstractmethod
    def run(self, data: Datasets) -> list[Order]:
        """Individual strategy run on each epoch, returns a list of orders"""
        pass
