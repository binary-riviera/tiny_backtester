from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Optional
from .backtester_types import Order, MarketData


class Strategy(ABC):
    tickers: set[str]
    portfolio: dict[str, int] = defaultdict(int)
    funds: int = 10000
    _counters = {}

    def __init__(self):
        cls = self.__class__
        Strategy._counters.setdefault(cls, 0)
        Strategy._counters[cls] += 1
        self._id = Strategy._counters[cls]
        self.label = f"{cls.__name__}_{self._id}"

    @abstractmethod
    def preload(self, data: MarketData) -> None:
        """Calculate new columns on data"""
        pass

    @abstractmethod
    def run(self, data: MarketData) -> Optional[list[Order]]:
        """Individual strategy run on each epoch, returns a list of orders"""
        pass
