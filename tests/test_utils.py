from tiny_backtester.strategy import Strategy
from tiny_backtester.utils.backtester_types import MarketData
import numpy as np
import pandas as pd


def get_test_strategy(tickers: set[str], funds: int, portfolio: dict[str, int] | None = None):
    class TestStrategy(Strategy):
        def __init__(self, tickers: set[str], funds: int):
            super().__init__()
            self.tickers = tickers
            self.funds = np.float64(funds)
            if portfolio:
                self.portfolio = portfolio

        def precalc(self, data: MarketData):
            pass

        def run(self, data: MarketData):
            return None

    return TestStrategy(tickers, funds)


def get_test_market_data_precalc(ticker: str) -> MarketData:
    return {ticker: get_full_df()}


def get_full_df():
    return pd.DataFrame(
        data={
            "open": [1.0, 2.0, 3.0, 4.0],
            "high": [1.0, 2.0, 3.0, 4.0],
            "low": [1.0, 2.0, 3.0, 4.0],
            "close": [1.0, 2.0, 3.0, 4.0],
            "volume": [100, 100, 100, 100],
            "slippage": [0.1, 0.1, 0.1, 0.1],
            "midpoint": [1.0, 2.0, 3.0, 4.0],
            "spread": [0.1, 0.1, 0.1, 0.1],
        },
        index=pd.date_range("1/1/2000", periods=4, freq="min"),
    )


def get_latest_df():
    return pd.DataFrame(
        data={
            "open": [0.5],
            "high": [1.0],
            "low": [0.5],
            "close": [1.0],
            "slippage": [0.001],
            "midpoint": [0.75],
            "spread": [0.01],
        }
    ).iloc[0]


def get_df_input() -> pd.DataFrame:
    return pd.DataFrame(
        data={
            "open": [1.0, 2.0, 3.0, 4.0],
            "high": [1.0, 2.0, 3.0, 4.0],
            "low": [1.0, 2.0, 3.0, 4.0],
            "close": [1.0, 2.0, 3.0, 4.0],
            "volume": [100, 100, 100, 100],
        },
        index=pd.date_range("1/1/2000", periods=4, freq="min"),
    )
