from tiny_backtester.utils.math_utils import get_average_entry_price, get_execution_price
import numpy as np
import pandas as pd


def test_get_execution_price():
    row1 = pd.Series(data={"slippage": 0.01, "midpoint": 5.0, "spread": 0.01})
    buy_price = get_execution_price("buy", row1)
    assert buy_price.round(2) == 5.06
    sell_price = get_execution_price("sell", row1)
    assert sell_price.round(2) == 4.95


def test_get_average_entry_price():
    # simple example
    q1 = 100
    p1 = np.float64(10.0)
    q2 = 100
    p2 = np.float64(20.0)
    assert get_average_entry_price(p1, p2, q1, q2) == 15.0
    # more complicated example
    q1 = 10
    p1 = np.float64(10.0)
    q2 = 100
    p2 = np.float64(5.0)
    assert get_average_entry_price(p1, p2, q1, q2).round(2) == 5.45
