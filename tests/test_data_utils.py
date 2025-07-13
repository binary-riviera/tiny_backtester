from datetime import datetime, timedelta
import pandas as pd
import pytest
from tiny_backtester.backtester_exception import BacktesterException
from unittest.mock import patch
from tiny_backtester.data_utils import (
    is_regularly_spaced,
    load_timeseries,
    resample_market_data,
)


def get_timeseries_dataframe(interval: str = "min"):
    index = pd.date_range("1/1/2000", periods=10, freq=interval)
    return pd.DataFrame({"col1": range(10)}, index=index)


def test_load_timeseries_dataframe_valid():
    valid_df = pd.DataFrame(
        {
            "datetime": pd.date_range("1/1/2000", periods=5, freq="min"),
            "open": [1, 2, 3, 4, 5],
            "high": [1, 2, 3, 4, 5],
            "low": [1, 2, 3, 4, 5],
            "close": [1, 2, 3, 4, 5],
        }
    )
    (ticker, _) = load_timeseries(valid_df, "TEST")
    assert ticker == "TEST"


def test_load_timeseries_dataframe_missing_cols():
    invalid_df = pd.DataFrame(
        {
            "datetime": pd.date_range("1/1/2000", periods=5, freq="min"),
            "wrong": [1, 2, 3, 4, 5],
        }
    )
    with pytest.raises(BacktesterException, match="missing columns:*"):
        load_timeseries(invalid_df, "TEST")


def test_load_timeseries_wrong_data_source_type():
    with pytest.raises(BacktesterException, match="data_source must be filepath or DataFrame"):
        load_timeseries(1.0, "TEST")  # type: ignore


def test_load_timeseries_is_irregular():
    now = datetime.now()
    invalid_df = pd.DataFrame(
        {
            "open": [1, 2, 3],
            "high": [1, 2, 3],
            "low": [1, 2, 3],
            "close": [1, 2, 3],
        },
        index=pd.Index([now, now + timedelta(1), now + timedelta(22)], name="datetime"),
    )
    with pytest.raises(BacktesterException, match="time series is irregular"):
        load_timeseries(invalid_df, "TEST", check_datetime_spacing=True)


def test_load_timeseries_no_ticker():
    valid_df = pd.DataFrame(
        {
            "datetime": pd.date_range("1/1/2000", periods=5, freq="min"),
            "open": [1, 2, 3, 4, 5],
            "high": [1, 2, 3, 4, 5],
            "low": [1, 2, 3, 4, 5],
            "close": [1, 2, 3, 4, 5],
        }
    )
    with pytest.raises(BacktesterException, match="ticker must be provided for DataFrame data"):
        load_timeseries(valid_df)


def test_load_timeseries_csv():
    valid_df = pd.DataFrame(
        {
            "datetime": pd.date_range("1/1/2000", periods=5, freq="min"),
            "open": [1, 2, 3, 4, 5],
            "high": [1, 2, 3, 4, 5],
            "low": [1, 2, 3, 4, 5],
            "close": [1, 2, 3, 4, 5],
        }
    )
    with patch("pandas.read_csv") as mock_method:
        mock_method.return_value = valid_df
        (ticker, _) = load_timeseries("test.csv")
        assert ticker == "test"
    mock_method.assert_called_once_with("test.csv", engine="c", index_col="datetime")


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


def test_resample_market_data_invalid_resample():
    df1 = get_timeseries_dataframe("1d")
    df2 = get_timeseries_dataframe("2d")
    with pytest.raises(BacktesterException, match="unsupported sampling type"):
        resample_market_data({"1": df1, "2": df2}, "foobar")  # type: ignore
