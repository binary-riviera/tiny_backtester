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

        def precalc(self, data):
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
                "volume": [100, 100, 100],
                "slippage": [0.1, 0.1, 0.1],
                "midpoint": [1.0, 1.0, 1.0],
                "spread": [0.1, 0.1, 0.1],
            }
        )
    }


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
    order = Order("TEST", "buy", 1)
    market_data = get_test_market_data("TEST")
    executed_order = engine.execute_order(strategy, order, cur_data=market_data)
    # assert executed_order.price == 1.0
    assert executed_order.quantity == 1
    assert executed_order.ticker == "TEST"
    assert executed_order.status == "filled"


def test_execute_order_buy_invalid():
    engine = Engine()
    strategy = get_test_strategy(set(), 1)
    order = Order("TEST", "buy", 100)
    market_data = get_test_market_data("TEST")
    executed_order = engine.execute_order(strategy, order, cur_data=market_data)
    # assert executed_order.price == 1.0
    assert executed_order.quantity == 100
    assert executed_order.ticker == "TEST"
    assert executed_order.status == "rejected"


def test_execute_order_sell_valid():
    engine = Engine()
    strategy = get_test_strategy(set(), 1, {"TEST": 20})
    order = Order("TEST", "sell", 10)
    market_data = get_test_market_data("TEST")
    executed_order = engine.execute_order(strategy, order, cur_data=market_data)
    # assert executed_order.price == 1.0
    assert executed_order.quantity == 10
    assert executed_order.ticker == "TEST"
    assert executed_order.status == "filled"
    assert strategy.portfolio["TEST"] == 10


def test_execute_order_sell_invalid():
    engine = Engine()
    strategy = get_test_strategy(set(), 1, {"TEST": 1})
    order = Order("TEST", "sell", 10)
    market_data = get_test_market_data("TEST")
    executed_order = engine.execute_order(strategy, order, cur_data=market_data)
    # assert executed_order.price == 1.0
    assert executed_order.quantity == 10
    assert executed_order.ticker == "TEST"
    assert executed_order.status == "rejected"
    assert strategy.portfolio["TEST"] == 1


def test_execute_order_invalid_order_type():
    engine = Engine()
    strategy = get_test_strategy(set(), 1)
    order = Order("TEST", "foo", 1)  # type: ignore
    market_data = get_test_market_data("TEST")
    executed_order = engine.execute_order(strategy, order, cur_data=market_data)
    assert executed_order.status == "unsupported"
