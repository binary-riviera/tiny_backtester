from datetime import datetime, timedelta
import pandas as pd
from tiny_backtester.data_utils import is_regularly_spaced, resample_market_data


def get_timeseries_dataframe(interval: str = "min"):
    index = pd.date_range("1/1/2000", periods=10, freq=interval)
    return pd.DataFrame({"col1": range(10)}, index=index)


def test_is_regularly_spaced_true():
    now = datetime.now()
    df = pd.DataFrame.from_dict(
        {now: [1, 2, 3], now + timedelta(1): [2, 3, 4], now + timedelta(2): [4, 5, 6]},
        orient="index",
    )
    assert is_regularly_spaced(df)


def test_is_regularly_space_false():
    now = datetime.now()
    df = pd.DataFrame.from_dict(
        {now: [1, 2, 3], now + timedelta(1): [2, 3, 4], now + timedelta(5): [4, 5, 6]},
        orient="index",
    )
    assert not is_regularly_spaced(df)


def test_resample_market_data_upsample():
    df1 = get_timeseries_dataframe("1d")
    df2 = get_timeseries_dataframe("2d")

    res = resample_market_data({"1": df1, "2": df2}, "upsample")
    assert len(res["1"]) == 10
    assert len(res["2"]) == 19
    assert pd.Timedelta(res["2"].index[1] - res["2"].index[0]) == pd.Timedelta("1d")


def test_resample_market_data_downsample():
    df1 = get_timeseries_dataframe("1d")
    df2 = get_timeseries_dataframe("2d")
    res = resample_market_data({"1": df1, "2": df2}, "downsample")
    assert len(res["1"]) == 5
    assert len(res["2"]) == 10
    assert pd.Timedelta(res["1"].index[1] - res["1"].index[0]) == pd.Timedelta("2d")
