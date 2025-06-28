from typing import Optional
from pandas import DataFrame, read_csv
from pathlib import Path
import numpy as np

from tiny_backtester.constants import MANDATORY_DF_COLUMNS
from .backtester_exception import BacktesterException


def load_csv(
    filepath: str, ticker: Optional[str], check_datetime_spacing=True
) -> tuple[str, DataFrame]:
    df = read_csv(filepath, engine="c", index_col="datetime")
    df.columns.str.lower()
    # TODO: set Datetime as datetime data type
    if missing_cols := MANDATORY_DF_COLUMNS - set(df.columns):
        raise BacktesterException(f"missing columns: {missing_cols}")
    if check_datetime_spacing and not is_regularly_spaced(df):
        raise BacktesterException("time series is irregular")
    return (ticker or Path(filepath).stem, df)


def is_regularly_spaced(df: DataFrame) -> np.bool:
    diff = np.diff(df.index.to_numpy())
    return np.all(diff == diff[0])
