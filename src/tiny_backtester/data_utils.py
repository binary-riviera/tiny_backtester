from pathlib import Path
from typing import Optional
import pandas as pd
import numpy as np

from tiny_backtester.backtester_exception import BacktesterException
from tiny_backtester.constants import MANDATORY_DF_COLUMNS


def load_timeseries(
    data_source: str | pd.DataFrame, ticker: Optional[str], check_datetime_spacing=True
) -> tuple[str, pd.DataFrame]:
    if type(data_source) is str:
        ticker = ticker or Path(data_source).stem
        data_source = pd.read_csv(data_source, engine="c", index_col="datetime")
    elif type(data_source) is pd.DataFrame:
        if not ticker:
            raise BacktesterException("ticker must be provided for DataFrame data")
    else:
        raise BacktesterException("data_source must be filepath or DataFrame")

    data_source.columns.str.lower()
    # TODO: set Datetime as datetime data type
    if missing_cols := MANDATORY_DF_COLUMNS - set(data_source.columns):
        raise BacktesterException(f"missing columns: {missing_cols}")
    if check_datetime_spacing and not is_regularly_spaced(data_source):
        raise BacktesterException("time series is irregular")
    return (ticker, data_source)


def is_regularly_spaced(df: pd.DataFrame) -> np.bool:
    diff = np.diff(df.index.to_numpy())
    return np.all(diff == diff[0])


def resample_market_data(
    dataframes: list[pd.DataFrame], resample: str
) -> list[pd.DataFrame]:
    if resample == "upsample":  # upsample to highest res
        resample = max([np.diff(df.index.to_numpy())[0] for df in dataframes])
    elif resample == "downsample":  # downsample to lowest res
        resample = min([np.diff(df.index.to_numpy())[0] for df in dataframes])
    for df in dataframes:
        df.resample(resample)
    return dataframes
