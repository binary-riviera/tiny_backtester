from abc import ABC, abstractmethod
from backtester_types import Order, Dataset

class Strategy:

    @abstractmethod
    def preload(data: list[Dataset]) -> None:
        """Calculate new columns on data"""
       pass 

    @abstractmethod
    def run(self, data: list[Dataset]) -> list[Order]:
        """Individual strategy run on each epoch, returns a list of orders"""
        pass

