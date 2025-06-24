from strategy import Strategy
from backtester_exception import BacktesterException
from backtester_types import Dataset
from dataloader import load_csv


class Engine:

    def __init__(self, funds: int = 10000):
        if funds <= 0:
            raise BacktesterException("Funds must be greater than 0")
        self.funds = funds
        self.data: Dataset = {}

    def load_dataset(self, filepath: str, ticker: str):
        if not filepath:
            raise BacktesterException("Must provide filepath")
        ticker, data = load_csv(filepath, ticker)
        self.data[ticker] = data

    def run(self, strategy: Strategy):
        if not self.data or len(self.data) == 0:
            raise BacktesterException("Must provide dataframe for backtesting")
        if not isinstance(strategy, Strategy):
            raise BacktesterException("strategy must be instance of class Strategy")
        if not strategy.tickers or len(strategy.tickers) == 0:
            raise BacktesterException("strategy must have tickers to run strategy on")
        if not strategy.tickers.issubset(set(self.data.keys())):
            raise BacktesterException(
                "data for tickers not found: "
                + str(strategy.tickers - set(self.data.keys()))
            )
        strategy.preload(self.data)
        print("preloaded data")
        # not sure if this is the best approach, but I'm going to find the shortest dataset in tickers then just step through that
        # later I can come up with a better approach
        length = min([len(self.data[ticker]) for ticker in strategy.tickers])
        for i in range(length + 1):
            cur_data = {
                ticker: self.data[ticker].iloc[:i] for ticker in strategy.tickers
            }
            orders = strategy.run(cur_data)
