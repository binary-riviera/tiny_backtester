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
    engine.load_timeseries(VALID_DATASET_PATH, "TEST")
    assert "TEST" in engine.market_data
    assert type(engine.market_data["TEST"]) == pd.DataFrame
    assert len(engine.market_data["TEST"]) == 100

    engine.run(strat=TestStrategy())
    assert "TEST_COLUMN" in engine.market_data["TEST"].columns
