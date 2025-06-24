from abc import ABC, abstractmethod
from backtester_types import Order, Dataset


class Strategy(ABC):
    tickers: set[str]

    @abstractmethod
    def preload(self, data: Dataset) -> None:
        """Calculate new columns on data"""
        pass

    @abstractmethod
    def run(self, data: Dataset) -> list[Order]:
        """Individual strategy run on each epoch, returns a list of orders"""
        pass
