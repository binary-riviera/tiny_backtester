from strategy import Strategy
from pandas import DataFrame
from backtester_exception import BacktesterException
from backtester_types import Dataset
from dataloader import load_csv

class Engine():

    def __init__(self, funds: int = 10000):
        if funds <= 0: raise BacktesterException('Funds must be greater than 0')
        self.funds = funds
        self.data = []

    def load_dataset(self, filepath: str, symbol: str):
        if not filepath: raise BacktesterException('Must provide filepath')
        self.data.append(load_csv(filepath, symbol) 

    def run(self, strategy: Strategy):
        if self.data is None or len(self.data) == 0: raise BacktesterException('Must provide dataframe for backtesting')
        strategy.preload(self.data)
        print('preloaded data')

