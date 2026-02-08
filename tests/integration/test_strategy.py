from tiny_backtester.utils.backtester_types import MarketData, Order
from tiny_backtester.engine import Engine
import pandas as pd

from tiny_backtester.strategy import Strategy

VALID_DATASET_PATH = "tests/integration/static/TEST_valid.csv"


class TestStrategy(Strategy):

    tickers = {"TEST"}

    def precalc(self, data: MarketData):
        df = data["TEST"]
        df["TEST_COLUMN"] = 1

    def run(self, data: MarketData):
        return [Order(ticker="TEST", type="buy", quantity=1)]


def test_load_and_run_strategy():
    engine = Engine()
    df = pd.read_csv(VALID_DATASET_PATH, index_col="datetime")
    df.index = pd.to_datetime(df.index)
    engine.load_ts("TEST", df)
    assert "TEST" in engine.market_data
    assert type(engine.market_data["TEST"]) == pd.DataFrame
    assert len(engine.market_data["TEST"]) == 100
    assert list(engine.market_data["TEST"].columns) == [
        "open",
        "high",
        "low",
        "close",
        "volume",
        "midpoint",
        "slippage",
        "spread",
    ]

    results = engine.run(strat=TestStrategy())
    assert "TEST_COLUMN" in engine.market_data["TEST"].columns
    assert "positions" in results
    assert "orders" in results
    assert len(results["positions"]) == 1
    assert len(results["orders"]) > 0  # we should have at least 1 order filled
    filled_order_len = len(results["orders"][results["orders"]["status"] == "filled"])
    assert filled_order_len + 1 == len(results["positions"]["TEST"])
