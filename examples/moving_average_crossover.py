from tiny_backtester.backtester_types import Datasets
from tiny_backtester.strategy import Strategy


class MovingAverageCrossover(Strategy):

    def __init__(self, ticker: str):
        super().__init__()
        self.ticker = ticker

    def preload(self, data: Datasets):
        df = data[self.ticker]
        df["Mean"] = df[["High", "Low"]].mean(axis=1)
        df["Moving Average 10"] = df["Mean"].rolling(10, closed="both").mean()
        df["Moving Average 60"] = df["Mean"].rolling(60, closed="both").mean()

    def run(self, data: Datasets):
        df = data[self.ticker]
        last_row = df.iloc[-1]


if __name__ == "__main__":
    mac = MovingAverageCrossover("GOOG")
    print(mac.label)
