import numpy as np
import pandas as pd

from tiny_backtester.utils.backtester_types import OrderType


def get_execution_price(quantity: int, type: OrderType, row: pd.Series) -> np.float64:
    if type == "buy":
        return np.float64((row["midpoint"] + 0.5 * row["spread"]) * (1 + row["slippage"]))
    elif type == "sell":
        return np.float64((row["midpoint"] - 0.5 * row["spread"]) * (1 - row["slippage"]))
    return np.nan


def get_average_entry_price(p1: np.float64, p2: np.float64, q1: int, q2: int) -> np.float64:
    return (p1 * q1 + p2 * q2) / (q1 + q2)
