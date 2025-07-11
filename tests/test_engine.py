import pandas as pd
import numpy as np
from tiny_backtester.backtester_exception import BacktesterException
from tiny_backtester.backtester_types import ExecutedOrder, Order, Position
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


def get_test_market_data_precalc(ticker):
    return {
        ticker: pd.DataFrame(
            data={
                "high": [1.0, 2.0, 3.0, 4.0],
                "low": [1.0, 2.0, 3.0, 4.0],
                "close": [1.0, 2.0, 3.0, 4.0],
                "volume": [100, 100, 100, 100],
                "slippage": [0.1, 0.1, 0.1, 0.1],
                "midpoint": [1.0, 2.0, 3.0, 4.0],
                "spread": [0.1, 0.1, 0.1, 0.1],
            }
        )
    }


def get_test_market_data(ticker):
    return {
        ticker: pd.DataFrame(
            data={
                "high": [1.0, 2.0, 3.0, 4.0],
                "low": [1.0, 2.0, 3.0, 4.0],
                "close": [1.0, 2.0, 3.0, 4.0],
                "volume": [100, 100, 100, 100],
            }
        )
    }


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
    market_data = get_test_market_data_precalc("TEST")
    executed_order = engine.execute_order(strategy, order, cur_data=market_data)
    # assert executed_order.price == 1.0
    assert executed_order.quantity == 1
    assert executed_order.ticker == "TEST"
    assert executed_order.status == "filled"


def test_execute_order_buy_invalid():
    engine = Engine()
    strategy = get_test_strategy(set(), 1)
    order = Order("TEST", "buy", 100)
    market_data = get_test_market_data_precalc("TEST")
    executed_order = engine.execute_order(strategy, order, cur_data=market_data)
    # assert executed_order.price == 1.0
    assert executed_order.quantity == 100
    assert executed_order.ticker == "TEST"
    assert executed_order.status == "rejected"


def test_execute_order_sell_valid():
    engine = Engine()
    strategy = get_test_strategy(set(), 1, {"TEST": 20})
    order = Order("TEST", "sell", 10)
    market_data = get_test_market_data_precalc("TEST")
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
    market_data = get_test_market_data_precalc("TEST")
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
    market_data = get_test_market_data_precalc("TEST")
    executed_order = engine.execute_order(strategy, order, cur_data=market_data)
    assert executed_order.status == "unsupported"


def test_get_average_entry_price():
    # simple example
    q1 = 100
    p1 = np.float64(10.0)
    q2 = 100
    p2 = np.float64(20.0)
    assert Engine().get_average_entry_price(p1, p2, q1, q2) == 15.0
    # more complicated example
    q1 = 10
    p1 = np.float64(10.0)
    q2 = 100
    p2 = np.float64(5.0)
    assert Engine().get_average_entry_price(p1, p2, q1, q2).round(2) == 5.45


def test_get_position_default():
    last_pos = Position()
    order = ExecutedOrder(
        last_pos.time + pd.Timedelta(1), "TEST", "buy", 10, np.float64(1.0), "filled"
    )
    pos = Engine.get_position(last_pos, order, get_latest_df())
    assert pos.quantity == 10
    assert pos.entry_price == 1.0
    assert pos.fill_price == 1.0
    assert pos.realised_pnl == 0.0
    assert pos.unrealised_pnl != 0.0


def test_get_position():
    last_pos = Position(pd.Timestamp.min, 10, np.float64(10.0), np.float64(8.0))
    order = ExecutedOrder(
        last_pos.time + pd.Timedelta(1), "TEST", "buy", 5, np.float64(15.0), "filled"
    )
    pos = Engine.get_position(last_pos, order, get_latest_df())
    assert pos.quantity == 15
    assert np.round(pos.entry_price, 2) == 11.67
    assert pos.fill_price == 15.0
    assert pos.realised_pnl == 0.0
    assert pos.unrealised_pnl != 0.0


def test_get_position_sell():
    last_pos = Position(pd.Timestamp.min, 10, np.float64(10.0), np.float64(8.0))
    order = ExecutedOrder(
        last_pos.time + pd.Timedelta(1), "TEST", "sell", 5, np.float64(15.0), "filled"
    )
    pos = Engine.get_position(last_pos, order, get_latest_df())
    assert pos.quantity == 5
    assert pos.entry_price == 10.0
    assert pos.fill_price == 15.0
    assert pos.realised_pnl == 25.0
    assert pos.unrealised_pnl != 0.0


def test_get_position_sell_reset_entry_price():
    last_pos = Position(pd.Timestamp.min, 10, np.float64(10.0), np.float64(8.0))
    order = ExecutedOrder(
        last_pos.time + pd.Timedelta(1), "TEST", "sell", 10, np.float64(15.0), "filled"
    )
    pos = Engine.get_position(last_pos, order, get_latest_df())
    assert pos.quantity == 0
    assert pos.entry_price == 0.0
    assert pos.fill_price == 15.0
    assert pos.realised_pnl == 50.0
    assert pos.unrealised_pnl != 0.0
