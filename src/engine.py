from strategy import Strategy
from pandas import DataFrame
from backtester_exception import BacktesterException
from backtester_types import Dataset

class Engine():

    def __init__(self, data: list[Dataset] | Dataset, funds: int = 10000):
        if funds <= 0: raise BacktesterException('Funds must be greater than 0')
        if data is None: raise BacktesterException('Must provide dataframe for backtesting')
        self.data = data if isinstance(data, list) else [data]

    def run(self, strategy: Strategy):
        pass
