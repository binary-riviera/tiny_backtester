from pandas import read_csv
import csv
from pathlib import Path
from backtester_utils import DF_COLUMNS
from backtester_types import Dataset
import numpy as np
from backtester_exception import BacktesterException

def load_csv(filepath: str, symbol: str, check_datetime_spacing=True):
    # TODO: add header validation???
    df = read_csv(filepath, engine='c', use_cols=DF_COLUMNS, index_col='Datetime')
    if check_datetime_spacing and not is_regularly_spaced(df):
        raise BacktesterException('Time series is irregular')
    symbol = symbol or Path(filepath).stem # use the filename as the symbol if not provided
    return Dataset(ticker=symbol, data=df)

def is_regularly_spaced(df: DataFrame):
    diff = np.diff(df.index.to_numpy())
    return np.all(diff == dif[0])
