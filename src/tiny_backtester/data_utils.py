from pathlib import Path
from typing import Optional
import pandas as pd
import numpy as np

from tiny_backtester.backtester_exception import BacktesterException
from tiny_backtester.backtester_types import ResampleType
from tiny_backtester.constants import MANDATORY_DF_COLUMNS


def load_timeseries(
    data_source: str | pd.DataFrame, ticker: Optional[str], check_datetime_spacing=True
) -> tuple[str, pd.DataFrame]:
    if type(data_source) is str:
        df = pd.read_csv(data_source, engine="c", index_col="datetime")
        ticker = ticker or Path(data_source).stem
    elif type(data_source) is pd.DataFrame:
        df = data_source
        if not ticker:
            raise BacktesterException("ticker must be provided for DataFrame data")
    else:
        raise BacktesterException("data_source must be filepath or DataFrame")

    df.columns.str.lower()
    # TODO: set Datetime as datetime data type
    if missing_cols := MANDATORY_DF_COLUMNS - set(df.columns):
        raise BacktesterException(f"missing columns: {missing_cols}")
    if check_datetime_spacing and not is_regularly_spaced(df):
        raise BacktesterException("time series is irregular")
    return (ticker, df)


def is_regularly_spaced(df: pd.DataFrame) -> np.bool:
    diff = np.diff(df.index.to_numpy())
    return np.all(diff == diff[0])


def resample_market_data(
    dataframes: list[pd.DataFrame], resampleType: ResampleType
) -> list[pd.DataFrame]:
    if resampleType == "upsample":
        pass
    else:
        pass
    return dataframes
