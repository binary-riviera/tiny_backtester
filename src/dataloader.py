from pandas import read_csv
import csv
from backtester_utils import DF_COLUMNS

def load_csv(filepath: str):
    # TODO: add header validation???
    return read_csv(filepath, engine='c', use_cols=DF_COLUMNS, index_col='Datetime')

