from typing import Literal, Optional
import numpy as np
import pandas as pd
import pandera.pandas as pa
import pandera.typing as pat
import logging

from pandas.tseries.frequencies import to_offset
from tiny_backtester.utils.backtester_exception import BacktesterException
from tiny_backtester.utils.backtester_types import CalendarType, OrderType, TimeSeries

logger = logging.getLogger("tiny_backtester")

# pricing parameters / options
k: float = 0.5  # slippage sensitivity constant

def get_execution_price(type: OrderType, row: pd.Series, slippage: bool = False) -> np.float64:
    if type == "buy":
        slippage_mult = (1 + row["slippage"]) if slippage else 1
        return np.float64((row["midpoint"] + 0.5 * row["spread"]) * slippage_mult)
    elif type == "sell":
        slippage_mult = (1 - row["slippage"]) if slippage else 1
        return np.float64((row["midpoint"] - 0.5 * row["spread"]) * slippage_mult)
    return np.nan


def get_average_entry_price(p1: np.float64, p2: np.float64, q1: int, q2: int) -> np.float64:
    return (p1 * q1 + p2 * q2) / (q1 + q2)


def get_sampling_type(df: pat.DataFrame[TimeSeries], freq: str) -> Literal["upsample", "downsample"]:
    current_nanos = to_offset(df.index.inferred_freq)
    target_nanos = to_offset(freq)
    return "upsample" if target_nanos < current_nanos else "downsample"


@pa.check_types
def resample(df: pat.DataFrame[TimeSeries], cal: CalendarType, freq: str) -> pat.DataFrame[TimeSeries]:
    logger.debug(f"resampling df with calendar: {cal} frequency: {freq}")
    match (cal, get_sampling_type(df, freq)):
        case ("continuous_24_7", "upsample"):
            return df.resample(freq).ffill()
        case ("continuous_24_7", "downsample"):
            return df.resample(freq).agg(
                {
                    "open": "first",
                    "high": "max",
                    "low": "min",
                    "close": "last",
                    "volume": "sum",
                    "slippage": "mean",
                    "midpoint": "mean",  # TODO: is this right?
                    "spread": "mean",
                }
            )
        case _:
            raise BacktesterException("Unsupported resampling operation")
    return df


@pa.check_types
def calculate_spread(df: pat.DataFrame[TimeSeries]) -> pat.DataFrame[TimeSeries]:
    # implementation of "A Simple Implicit Measure of the Effective Bid-Ask Spread in an Efficient Market [1984], Roll"
    delta = np.diff(df["close"].to_numpy())
    cov = np.cov(delta[:-1], delta[1:])[0, 1]
    spread = 2 * np.sqrt(-cov) if cov < 0 else 0.0
    df["spread"] = spread
    logger.debug(f"calculated spread {spread}")
    return df


@pa.check_types
def process_df(
    df: pat.DataFrame[TimeSeries],
    cal: Optional[CalendarType] = None,
    resample_freq: Optional[str] = None,
) -> pat.DataFrame[TimeSeries]:
    if (cal is None) ^ (resample_freq is None):
        raise BacktesterException("Must provide both 'cal' and 'resample_freq' to resample")
    return (
        df.rename(columns=str.lower)
        .pipe(lambda d: d.assign(midpoint=(d["high"] + d["low"]) / 2) if "midpoint" not in d else d)
        .pipe(lambda d: d.assign(slippage=k / d["volume"]) if "slippage" not in d else d)
        .pipe(lambda d: calculate_spread(d) if "spread" not in d else d)
        .pipe(lambda d: resample(d, cal, resample_freq) if (cal and resample_freq) else d)
    )
