import pandas as pd
import numpy as np
from tests.test_utils import (
    get_latest_df,
    get_df_input,
    get_test_market_data_precalc,
    get_test_strategy,
)
from tiny_backtester.utils.backtester_exception import BacktesterException
from tiny_backtester.utils.backtester_types import ExecutedOrder, Order, Position
from tiny_backtester.engine import Engine
from pandas.testing import assert_frame_equal
import pytest


def test_run_no_funds():
    engine = Engine()
    strategy = get_test_strategy(set(), 0)
    with pytest.raises(BacktesterException, match="strategy funds must be greater than 0"):
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
    with pytest.raises(BacktesterException, match="strategy must have tickers to run strategy on"):
        engine.run(strategy)


def test_run_ticker_data_not_found():
    engine = Engine()
    engine.market_data = {"test": pd.DataFrame()}
    strategy = get_test_strategy({"invalid_ticker"}, 10000)
    with pytest.raises(BacktesterException, match="data for tickers not found: {'invalid_ticker'}"):
        engine.run(strategy)


def test_execute_order_buy_valid():
    engine = Engine()
    strategy = get_test_strategy(set(), 10000)
    order = Order("TEST", "buy", 1)
    market_data = get_test_market_data_precalc("TEST")
    executed_order = engine.execute_order(strategy, order, cur_data=market_data)
    assert type(executed_order.time) == pd.Timestamp
    assert executed_order.price > 4.0
    assert executed_order.quantity == 1
    assert executed_order.ticker == "TEST"
    assert executed_order.status == "filled"
    assert strategy.funds < 10000


def test_execute_order_buy_invalid():
    engine = Engine()
    strategy = get_test_strategy(set(), 1)
    order = Order("TEST", "buy", 100)
    market_data = get_test_market_data_precalc("TEST")
    executed_order = engine.execute_order(strategy, order, cur_data=market_data)
    assert type(executed_order.time) == pd.Timestamp
    assert executed_order.price > 4.0
    assert executed_order.quantity == 100
    assert executed_order.ticker == "TEST"
    assert executed_order.status == "rejected"
    assert strategy.funds == 1


def test_execute_order_sell_valid():
    engine = Engine()
    strategy = get_test_strategy(set(), 1, {"TEST": 20})
    order = Order("TEST", "sell", 10)
    market_data = get_test_market_data_precalc("TEST")
    executed_order = engine.execute_order(strategy, order, cur_data=market_data)
    assert type(executed_order.time) == pd.Timestamp
    assert executed_order.price < 4.0
    assert executed_order.quantity == 10
    assert executed_order.ticker == "TEST"
    assert executed_order.status == "filled"
    assert strategy.portfolio["TEST"] == 10
    assert strategy.funds > 1


def test_execute_order_sell_invalid():
    engine = Engine()
    strategy = get_test_strategy(set(), 1, {"TEST": 1})
    order = Order("TEST", "sell", 10)
    market_data = get_test_market_data_precalc("TEST")
    executed_order = engine.execute_order(strategy, order, cur_data=market_data)
    assert type(executed_order.time) == pd.Timestamp
    assert executed_order.price < 4.0
    assert executed_order.quantity == 10
    assert executed_order.ticker == "TEST"
    assert executed_order.status == "rejected"
    assert strategy.portfolio["TEST"] == 1
    assert strategy.funds == 1


def test_execute_order_invalid_order_type():
    engine = Engine()
    strategy = get_test_strategy(set(), 1)
    order = Order("TEST", "foo", 1)  # type: ignore
    market_data = get_test_market_data_precalc("TEST")
    executed_order = engine.execute_order(strategy, order, cur_data=market_data)
    assert executed_order.status == "unsupported"


def test_execute_order_buy_limit_valid():
    engine = Engine()
    strategy = get_test_strategy(set(), 1000)
    order = Order("TEST", "buy", 1, limit_price=10.0)
    market_data = get_test_market_data_precalc("TEST")
    executed_order = engine.execute_order(strategy, order, cur_data=market_data)
    assert executed_order.price > 1.0
    assert executed_order.quantity == 1
    assert executed_order.ticker == "TEST"
    assert executed_order.status == "filled"


def test_execute_order_buy_limit_invalid():
    engine = Engine()
    strategy = get_test_strategy(set(), 1000)
    order = Order("TEST", "buy", 1, limit_price=0.5)
    market_data = get_test_market_data_precalc("TEST")
    executed_order = engine.execute_order(strategy, order, cur_data=market_data)
    assert executed_order.price > 1.0
    assert executed_order.quantity == 1
    assert executed_order.ticker == "TEST"
    assert executed_order.status == "rejected"


def test_execute_order_sell_limit_valid():
    engine = Engine()
    strategy = get_test_strategy(set(), 1, {"TEST": 20})
    order = Order("TEST", "sell", 10, limit_price=0.1)
    market_data = get_test_market_data_precalc("TEST")
    executed_order = engine.execute_order(strategy, order, cur_data=market_data)
    print(executed_order)
    assert executed_order.price < 4.0
    assert executed_order.quantity == 10
    assert executed_order.ticker == "TEST"
    assert executed_order.status == "filled"
    assert strategy.portfolio["TEST"] == 10


def test_execute_order_sell_limit_invalid():
    engine = Engine()
    strategy = get_test_strategy(set(), 1, {"TEST": 1})
    order = Order("TEST", "sell", 10, limit_price=10.0)
    market_data = get_test_market_data_precalc("TEST")
    executed_order = engine.execute_order(strategy, order, cur_data=market_data)
    assert executed_order.price < 4.0
    assert executed_order.quantity == 10
    assert executed_order.ticker == "TEST"
    assert executed_order.status == "rejected"
    assert strategy.portfolio["TEST"] == 1


def test_get_position_default():
    last_pos = Position()
    order = ExecutedOrder(
        last_pos.time + pd.Timedelta(1), "TEST", "buy", 10, np.float64(1.0), "filled"
    )
    engine = Engine()
    pos = engine.get_position(last_pos, order, get_latest_df())
    assert pos.quantity == 10
    assert pos.entry_price == 1.0
    assert pos.fill_price == 1.0
    assert pos.realised_pnl == 0.0
    assert pos.unrealised_pnl != 0.0


def test_get_position_buy():
    last_pos = Position(pd.Timestamp.min, 10, np.float64(10.0), np.float64(8.0))
    order = ExecutedOrder(
        last_pos.time + pd.Timedelta(1), "TEST", "buy", 5, np.float64(15.0), "filled"
    )
    engine = Engine()
    pos = engine.get_position(last_pos, order, get_latest_df())
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
    engine = Engine()
    pos = engine.get_position(last_pos, order, get_latest_df())
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
    engine = Engine()
    pos = engine.get_position(last_pos, order, get_latest_df())
    assert pos.quantity == 0
    assert pos.entry_price == 0.0
    assert pos.fill_price == 15.0
    assert pos.realised_pnl == 50.0
    assert pos.unrealised_pnl == 0.0


def load_ts_valid():
    engine = Engine()
    engine.load_ts("TEST", get_df_input())
    assert len(engine.market_data) == 1
    assert "TEST" in engine.market_data
    assert_frame_equal(
        engine.market_data["TEST"], get_test_market_data_precalc("TEST")["TEST"], check_exact=True
    )
