from pathlib import Path
from typing import Literal, Optional
import pandas as pd
import numpy as np

from tiny_backtester.utils.backtester_exception import BacktesterException
from tiny_backtester.utils.backtester_types import MarketData
from tiny_backtester.utils.constants import MANDATORY_DF_COLUMNS


def load_timeseries(
    source: str | pd.DataFrame, ticker: Optional[str] = None, check_datetime_spacing=False
) -> tuple[str, pd.DataFrame]:
    if type(source) is str:
        ticker = ticker or Path(source).stem
        source = pd.read_csv(source, engine="c", index_col="datetime")
        source.index = pd.to_datetime(source.index)
    elif type(source) is pd.DataFrame:
        if not ticker:
            raise BacktesterException("ticker must be provided for DataFrame data")
    else:
        raise BacktesterException("data_source must be filepath or DataFrame")
    # TODO: verify index
    source.columns = source.columns.str.lower()
    if missing_cols := MANDATORY_DF_COLUMNS - set(source.columns):
        raise BacktesterException(f"missing columns: {missing_cols}")
    if check_datetime_spacing and not is_regularly_spaced(source):
        raise BacktesterException("time series is irregular")
    return (ticker, source)


def is_regularly_spaced(df: pd.DataFrame) -> np.bool:
    diff = np.diff(df.index.to_numpy())
    return np.all(diff == diff[0])


# TODO: this entire function is unfit for purpose, rewrite to use pandas_market_calendars


def resample_market_data(
    market_data: MarketData, resample: Literal["upsample", "downsample"]
) -> MarketData:
    if len(market_data.items()) <= 1:
        return market_data
    intervals = [df.index[1] - df.index[0] for df in market_data.values()]
    if resample == "upsample":  # use the samllest interval
        return {k: df.resample(min(intervals)).ffill() for k, df in market_data.items()}
    elif resample == "downsample":  # use the largest interval
        return {k: df.resample(max(intervals)).mean() for k, df in market_data.items()}
    else:
        raise BacktesterException("unsupported sampling type")
    # TODO: implement custom sampling here
    # but will need to handle both up and downsampling and apply ffill or mean accordingly
