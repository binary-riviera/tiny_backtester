from pandas import DataFrame, read_csv
from pathlib import Path
from backtester_utils import DF_COLUMNS
from backtester_types import Dataset
import numpy as np
from backtester_exception import BacktesterException

def load_csv(filepath: str, symbol: str, check_datetime_spacing=True) -> tuple[str, DataFrame]:
    # TODO: add header validation???
    df = read_csv(filepath, engine='c', usecols=list(DF_COLUMNS), index_col='Datetime')
    if check_datetime_spacing and not is_regularly_spaced(df):
        raise BacktesterException('Time series is irregular')
    symbol = symbol or Path(filepath).stem # use the filename as the symbol if not provided
    return (symbol, df)

def is_regularly_spaced(df: DataFrame):
    diff = np.diff(df.index.to_numpy())
    return np.all(diff == diff[0])
