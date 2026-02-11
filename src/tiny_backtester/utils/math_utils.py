import numpy as np
import pandas as pd
import pandera.pandas as pa
import pandera.typing as pat

from tiny_backtester.utils.backtester_types import OrderType, TimeSeries

# pricing parameters / options
k: float = 0.5  # slippage sensitivity constant


def get_execution_price(type: OrderType, row: pd.Series) -> np.float64:
    if type == "buy":
        return np.float64((row["midpoint"] + 0.5 * row["spread"]) * (1 + row["slippage"]))
    elif type == "sell":
        return np.float64((row["midpoint"] - 0.5 * row["spread"]) * (1 - row["slippage"]))
    return np.nan


def get_average_entry_price(p1: np.float64, p2: np.float64, q1: int, q2: int) -> np.float64:
    return (p1 * q1 + p2 * q2) / (q1 + q2)


@pa.check_types
def calculate_spread(df: pat.DataFrame[TimeSeries]) -> pat.DataFrame[TimeSeries]:
    if "spread" not in df:
        # implementation of "A Simple Implicit Measure of the Effective Bid-Ask Spread in an Efficient Market [1984], Roll"
        delta = np.diff(df["close"].to_numpy())
        cov = np.cov(delta)
        spread = 2 * np.sqrt(-cov) if cov < 0 else 0.0
        df["spread"] = spread
    return df


@pa.check_types
def process_df(df: pat.DataFrame[TimeSeries]) -> pat.DataFrame[TimeSeries]:
    return (
        df.rename(columns=str.lower)
        .pipe(lambda d: d.assign(midpoint=(d["high"] + d["low"]) / 2) if "midpoint" not in d else d)
        .pipe(lambda d: d.assign(slippage=k / d["volume"]) if "slippage" not in d else d)
        .pipe(calculate_spread)
    )
