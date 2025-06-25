from typing import Optional
from pandas import DataFrame, read_csv
from pathlib import Path
from .utils import DF_COLUMNS
import numpy as np
from .backtester_exception import BacktesterException


def load_csv(
    filepath: str, ticker: Optional[str], check_datetime_spacing=True
) -> tuple[str, DataFrame]:
    df = read_csv(filepath, engine="c", usecols=list(DF_COLUMNS), index_col="Datetime")
    if check_datetime_spacing and not is_regularly_spaced(df):
        raise BacktesterException("time series is irregular")
    ticker = (
        ticker or Path(filepath).stem
    )  # use the filename as the symbol if not provided
    return (ticker, df)


def is_regularly_spaced(df: DataFrame) -> np.bool:
    diff = np.diff(df.index.to_numpy())
    return np.all(diff == diff[0])
