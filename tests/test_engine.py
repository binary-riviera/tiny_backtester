import pandas as pd
import numpy as np
from tiny_backtester.backtester_exception import BacktesterException
from tiny_backtester.backtester_types import Order, OrderStatus, OrderType
from tiny_backtester.engine import Engine
import pytest

from tiny_backtester.strategy import Strategy


def get_test_strategy(tickers, funds, portfolio=None):
    class TestStrategy(Strategy):
        def __init__(self, tickers, funds):
            super().__init__()
            self.tickers = tickers
            self.funds = np.float64(funds)
            if portfolio:
                self.portfolio = portfolio

        def preload(self, data):
            pass

        def run(self, data):
            return None

    return TestStrategy(tickers, funds)


def get_test_market_data(ticker):
    return {
        ticker: pd.DataFrame(
            data={
                "high": [1.0, 2.0, 3.0],
                "low": [1.0, 2.0, 3.0],
                "close": [1.0, 2.0, 3.0],
                "volume": 100,
            }
        )
    }


def test_load_timeseries_filepath_not_provided():
    engine = Engine()
    with pytest.raises(BacktesterException, match="must provide filepath"):
        engine.load_timeseries_from_csv("")


def test_run_no_funds():
    engine = Engine()
    strategy = get_test_strategy(set(), 0)
    with pytest.raises(
        BacktesterException, match="strategy funds must be greater than 0"
    ):
        engine.run(strategy)


def test_run_no_data():
    engine = Engine()
    engine.market_data = {}
    strategy = get_test_strategy(set(), 10000)
    with pytest.raises(BacktesterException, match="must provide data for backtesting"):
        engine.run(strategy)


def test_run_no_tickers():
    engine = Engine()
    engine.market_data = {"test": pd.DataFrame()}
    strategy = get_test_strategy(set(), 10000)
    with pytest.raises(
        BacktesterException, match="strategy must have tickers to run strategy on"
    ):
        engine.run(strategy)


def test_run_ticker_data_not_found():
    engine = Engine()
    engine.market_data = {"test": pd.DataFrame()}
    strategy = get_test_strategy({"invalid_ticker"}, 10000)
    with pytest.raises(
        BacktesterException, match="data for tickers not found: {'invalid_ticker'}"
    ):
        engine.run(strategy)


def test_execute_order_buy_valid():
    engine = Engine()
    strategy = get_test_strategy(set(), 10000)
    order = Order("TEST", OrderType.BUY, 1)
    market_data = get_test_market_data("TEST")
    executed_order = engine.execute_order(strategy, order, cur_data=market_data)
    # assert executed_order.price == 1.0
    assert executed_order.quantity == 1
    assert executed_order.ticker == "TEST"
    assert executed_order.status == OrderStatus.FILLED


def test_execute_order_buy_invalid():
    engine = Engine()
    strategy = get_test_strategy(set(), 1)
    order = Order("TEST", OrderType.BUY, 100)
    market_data = get_test_market_data("TEST")
    executed_order = engine.execute_order(strategy, order, cur_data=market_data)
    # assert executed_order.price == 1.0
    assert executed_order.quantity == 100
    assert executed_order.ticker == "TEST"
    assert executed_order.status == OrderStatus.REJECTED


def test_execute_order_sell_valid():
    engine = Engine()
    strategy = get_test_strategy(set(), 1, {"TEST": 20})
    order = Order("TEST", OrderType.SELL, 10)
    market_data = get_test_market_data("TEST")
    executed_order = engine.execute_order(strategy, order, cur_data=market_data)
    # assert executed_order.price == 1.0
    assert executed_order.quantity == 10
    assert executed_order.ticker == "TEST"
    assert executed_order.status == OrderStatus.FILLED
    assert strategy.portfolio["TEST"] == 10


def test_execute_order_sell_invalid():
    engine = Engine()
    strategy = get_test_strategy(set(), 1, {"TEST": 1})
    order = Order("TEST", OrderType.SELL, 10)
    market_data = get_test_market_data("TEST")
    executed_order = engine.execute_order(strategy, order, cur_data=market_data)
    # assert executed_order.price == 1.0
    assert executed_order.quantity == 10
    assert executed_order.ticker == "TEST"
    assert executed_order.status == OrderStatus.REJECTED
    assert strategy.portfolio["TEST"] == 1


def test_execute_order_invalid_order_type():
    engine = Engine()
    strategy = get_test_strategy(set(), 1)
    order = Order("TEST", OrderType.BUY_LIMIT, 1)
    market_data = get_test_market_data("TEST")
    executed_order = engine.execute_order(strategy, order, cur_data=market_data)
    assert executed_order.status == OrderStatus.UNSUPPORTED


def test_get_bid_ask_spread():
    engine = Engine()
    series = pd.Series([1, 2, 4, 1, 4, 5, 6, 7])
    bid_ask_spread = engine.get_bid_ask_spread(series)
    print(bid_ask_spread)
    print(type(bid_ask_spread))
    assert bid_ask_spread.round(3) == 3.729
