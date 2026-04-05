from tiny_backtester.utils.backtester_types import MarketData, Order
from tiny_backtester.engine import Engine
from tiny_backtester.strategy import Strategy
import pandas as pd
import cProfile

class MovingAverageCrossover(Strategy):

    def __init__(self, ticker: str):
        super().__init__()
        self.tickers = {ticker}

    def precalc(self, data: MarketData):
        df = data["TSLA"]
        df["mean"] = df[["high", "low"]].mean(axis=1)
        df["Moving Average 10"] = df["mean"].rolling(10, closed="both").mean()
        df["Moving Average 60"] = df["mean"].rolling(60, closed="both").mean()

    def run(self, data: MarketData):
        latest = data["TSLA"].iloc[-1]
        if latest["Moving Average 10"] > latest["Moving Average 60"]:
            return [Order("TSLA", "buy", 1)]
        elif latest["Moving Average 10"] < latest["Moving Average 60"]:
            return [Order("TSLA", "sell", 1)]


if __name__ == "__main__":
    mac = MovingAverageCrossover("TSLA")

    df = pd.read_csv("./examples/data/TSLA.csv", index_col="datetime")
    df.columns = df.columns.str.lower()
    df.index = pd.to_datetime(df.index)
    with cProfile.Profile() as pr:
        engine = Engine()
        engine.load_ts("TSLA", df)
        results = engine.run(mac)
        pr.print_stats()
        pr.dump_stats("mac.prof")
