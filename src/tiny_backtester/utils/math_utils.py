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


def get_execution_price(type: OrderType, row: pd.Series) -> np.float64:
    if type == "buy":
        return np.float64((row["midpoint"] + 0.5 * row["spread"]) * (1 + row["slippage"]))
    elif type == "sell":
        return np.float64((row["midpoint"] - 0.5 * row["spread"]) * (1 - row["slippage"]))
    return np.nan


def get_average_entry_price(p1: np.float64, p2: np.float64, q1: int, q2: int) -> np.float64:
    return (p1 * q1 + p2 * q2) / (q1 + q2)


def get_sampling_type(
    df: pat.DataFrame[TimeSeries], resample_freq: str
) -> Literal["upsample", "downsample"]:
    current_nanos = to_offset(df.index.inferred_freq)
    target_nanos = to_offset(resample_freq)
    return "upsample" if target_nanos < current_nanos else "downsample"


@pa.check_types
def resample(
    df: pat.DataFrame[TimeSeries], cal: CalendarType, resample_freq: str
) -> pat.DataFrame[TimeSeries]:
    logger.debug(f"resampling df with calendar: {cal} frequency: {resample_freq}")
    match (cal, get_sampling_type(df, resample_freq)):
        case ("continuous_24_7", "upsample"):
            return df.resample(resample_freq).ffill()
        case ("continuous_24_7", "downsample"):
            return df.resample(resample_freq).agg(
                {"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}
            )
        case _:
            raise BacktesterException("Unsupported resampling operation")
    return df


@pa.check_types
def calculate_spread(df: pat.DataFrame[TimeSeries]) -> pat.DataFrame[TimeSeries]:
    if "spread" not in df:
        # implementation of "A Simple Implicit Measure of the Effective Bid-Ask Spread in an Efficient Market [1984], Roll"
        delta = np.diff(df["close"].to_numpy())
        cov = np.cov(delta)
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
        .pipe(lambda d: resample(d, cal, resample_freq) if (cal and resample_freq) else d)
        .pipe(lambda d: d.assign(midpoint=(d["high"] + d["low"]) / 2) if "midpoint" not in d else d)
        .pipe(lambda d: d.assign(slippage=k / d["volume"]) if "slippage" not in d else d)
        .pipe(calculate_spread)
    )
