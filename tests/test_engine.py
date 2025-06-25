from pandas import DataFrame
from backtester_exception import BacktesterException
from backtester_types import Order, OrderStatus, OrderType
from engine import Engine
import pytest

from strategy import Strategy


def get_strategy(tickers, funds, portfolio=None):
    class TestStrategy(Strategy):
        def __init__(self, tickers, funds):
            super().__init__()
            self.tickers = tickers
            self.funds = funds
            if portfolio:
                self.portfolio = portfolio

        def preload(self, data):
            pass

        def run(self, data):
            return None

    return TestStrategy(tickers, funds)


def get_dataset(ticker):
    return {ticker: DataFrame(data={"Close": [1.0]})}


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
    engine.data = {}
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


def test_execute_order_buy_valid():
    engine = Engine()
    strategy = get_strategy(set(), 10000)
    order = Order("TEST", OrderType.BUY, 1)
    dataset = get_dataset("TEST")
    executed_order = engine.execute_order(strategy, order, cur_data=dataset)
    assert executed_order.price == 1.0
    assert executed_order.quantity == 1
    assert executed_order.ticker == "TEST"
    assert executed_order.status == OrderStatus.FILLED


def test_execute_order_buy_invalid():
    engine = Engine()
    strategy = get_strategy(set(), 1)
    order = Order("TEST", OrderType.BUY, 100)
    dataset = get_dataset("TEST")
    executed_order = engine.execute_order(strategy, order, cur_data=dataset)
    assert executed_order.price == 1.0
    assert executed_order.quantity == 100
    assert executed_order.ticker == "TEST"
    assert executed_order.status == OrderStatus.REJECTED


def test_execute_order_sell_valid():
    engine = Engine()
    strategy = get_strategy(set(), 1, {"TEST": 20})
    order = Order("TEST", OrderType.SELL, 10)
    dataset = get_dataset("TEST")
    executed_order = engine.execute_order(strategy, order, cur_data=dataset)
    assert executed_order.price == 1.0
    assert executed_order.quantity == 10
    assert executed_order.ticker == "TEST"
    assert executed_order.status == OrderStatus.FILLED
    assert strategy.portfolio["TEST"] == 10


def test_execute_order_sell_invalid():
    engine = Engine()
    strategy = get_strategy(set(), 1, {"TEST": 1})
    order = Order("TEST", OrderType.SELL, 10)
    dataset = get_dataset("TEST")
    executed_order = engine.execute_order(strategy, order, cur_data=dataset)
    assert executed_order.price == 1.0
    assert executed_order.quantity == 10
    assert executed_order.ticker == "TEST"
    assert executed_order.status == OrderStatus.REJECTED
    assert strategy.portfolio["TEST"] == 1


def test_execute_order_invalid_order_type():
    engine = Engine()
    strategy = get_strategy(set(), 1)
    order = Order("TEST", OrderType.BUY_LIMIT, 1)
    dataset = get_dataset("TEST")
    executed_order = engine.execute_order(strategy, order, cur_data=dataset)
    assert executed_order.status == OrderStatus.UNSUPPORTED
