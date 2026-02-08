from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Optional

from tiny_backtester.utils.backtester_types import Order, MarketData
from numpy import float64


class Strategy(ABC):
    tickers: set[str]
    portfolio: dict[str, int] = defaultdict(int)
    funds = float64(10000)

    @abstractmethod
    def precalc(self, data: MarketData) -> None:
        """Calculate new columns on data"""

    @abstractmethod
    def run(self, data: MarketData) -> Optional[list[Order]]:
        """Individual strategy run on each epoch, returns a list of orders"""
