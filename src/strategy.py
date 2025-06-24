from abc import ABC, abstractmethod
from backtester_types import Order, Dataset

class Strategy:

    @abstractmethod
    def run(self, data: list[Dataset]) -> list[Order]:
        pass

