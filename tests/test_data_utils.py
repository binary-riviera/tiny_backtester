from datetime import datetime, timedelta
from pandas import DataFrame

from tiny_backtester.data_utils import is_regularly_spaced


def test_is_regularly_spaced_true():
    now = datetime.now()
    df = DataFrame.from_dict(
        {now: [1, 2, 3], now + timedelta(1): [2, 3, 4], now + timedelta(2): [4, 5, 6]},
        orient="index",
    )
    assert is_regularly_spaced(df)


def test_is_regularly_space_false():
    now = datetime.now()
    df = DataFrame.from_dict(
        {now: [1, 2, 3], now + timedelta(1): [2, 3, 4], now + timedelta(5): [4, 5, 6]},
        orient="index",
    )
    assert not is_regularly_spaced(df)
