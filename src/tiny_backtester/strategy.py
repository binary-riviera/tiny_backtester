from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Optional

from tiny_backtester.constants import DEFAULT_FUNDS
from .backtester_types import Order, MarketData
from numpy import float64


class Strategy(ABC):
    tickers: set[str]
    portfolio: dict[str, int] = defaultdict(int)
    funds = float64(DEFAULT_FUNDS)
    _counters = {}

    def __init__(self):
        cls = self.__class__
        Strategy._counters.setdefault(cls, 0)
        Strategy._counters[cls] += 1
        self._id = Strategy._counters[cls]
        self.label = f"{cls.__name__}_{self._id}"

    def __repr__(self):
        return self.label

    @abstractmethod
    def preload(self, data: MarketData) -> None:
        """Calculate new columns on data"""

    @abstractmethod
    def run(self, data: MarketData) -> Optional[list[Order]]:
        """Individual strategy run on each epoch, returns a list of orders"""
