from pandas import DataFrame
from backtester_exception import BacktesterException
from engine import Engine
import pytest

from strategy import Strategy


def get_strategy(tickers, funds):
    class TestStrategy(Strategy):
        def __init__(self, tickers, funds):
            self.tickers = tickers
            self.funds = funds

        def preload(self, data):
            pass

        def run(self, data):
            return None

    return TestStrategy(tickers, funds)


def test_load_dataset_filepath_not_provided():
    engine = Engine()
    with pytest.raises(BacktesterException, match="must provide filepath"):
        engine.load_dataset("")


def test_run_no_funds():
    engine = Engine()
    strategy = get_strategy(set(), 0)
    with pytest.raises(
        BacktesterException, match="strategy funds must be greater than 0"
    ):
        engine.run(strategy)


def test_run_no_data():
    engine = Engine()
    strategy = get_strategy(set(), 10000)
    with pytest.raises(BacktesterException, match="must provide data for backtesting"):
        engine.run(strategy)


def test_run_no_tickers():
    engine = Engine()
    engine.data = {"test": DataFrame()}
    strategy = get_strategy(set(), 10000)
    with pytest.raises(
        BacktesterException, match="strategy must have tickers to run strategy on"
    ):
        engine.run(strategy)


def test_run_ticker_data_not_found():
    engine = Engine()
    engine.data = {"test": DataFrame()}
    strategy = get_strategy({"invalid_ticker"}, 10000)
    with pytest.raises(
        BacktesterException, match="data for tickers not found: {'invalid_ticker'}"
    ):
        engine.run(strategy)
