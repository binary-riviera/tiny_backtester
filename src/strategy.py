from abc import ABC, abstractmethod
from backtester_types import Order
from pandas import DataFrame

class Strategy:

    @abstractmethod
    def run(self, data: DataFrame) -> list[Order]:
        pass

