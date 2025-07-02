from pathlib import Path
from typing import Literal, Optional
import pandas as pd
import numpy as np

from tiny_backtester.backtester_exception import BacktesterException
from tiny_backtester.backtester_types import MarketData
from tiny_backtester.constants import MANDATORY_DF_COLUMNS


def load_timeseries(
    data_source: str | pd.DataFrame, ticker: Optional[str], check_datetime_spacing=True
) -> tuple[str, pd.DataFrame]:
    if type(data_source) is str:
        ticker = ticker or Path(data_source).stem
        data_source = pd.read_csv(data_source, engine="c", index_col="datetime")
        data_source.index = pd.to_datetime(data_source.index)
    elif type(data_source) is pd.DataFrame:
        if not ticker:
            raise BacktesterException("ticker must be provided for DataFrame data")
    else:
        raise BacktesterException("data_source must be filepath or DataFrame")
    if missing_cols := MANDATORY_DF_COLUMNS - set(data_source.columns):
        raise BacktesterException(f"missing columns: {missing_cols}")
    if check_datetime_spacing and not is_regularly_spaced(data_source):
        raise BacktesterException("time series is irregular")
    return (ticker, data_source)


def is_regularly_spaced(df: pd.DataFrame) -> np.bool:
    diff = np.diff(df.index.to_numpy())
    return np.all(diff == diff[0])


def resample_market_data(
    market_data: MarketData, resample: Literal["upsample", "downsample"]
) -> MarketData:
    intervals = [df.index[1] - df.index[0] for df in market_data.values()]
    if resample == "upsample":  # use the samllest interval
        return {k: df.resample(min(intervals)).ffill() for k, df in market_data.items()}
    elif resample == "downsample":  # use the largest interval
        return {k: df.resample(max(intervals)).mean() for k, df in market_data.items()}
    else:
        raise BacktesterException("unsupported sampling type")
    # TODO: implement custom sampling here
    # but will need to handle both up and downsampling and apply ffill or mean accordingly
