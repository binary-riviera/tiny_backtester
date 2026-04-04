from pandas.testing import assert_frame_equal
import pytest
from tests.test_utils import get_df_input, get_full_df
from tiny_backtester.utils.backtester_exception import BacktesterException
from tiny_backtester.utils.math_utils import (
    get_average_entry_price,
    get_execution_price,
    process_df,
)
import numpy as np
import pandas as pd


def test_get_execution_price():
    row1 = pd.Series(data={"slippage": 0.01, "midpoint": 5.0, "spread": 0.01})
    buy_price = get_execution_price("buy", row1)
    assert buy_price == 5.005
    sell_price = get_execution_price("sell", row1)
    assert sell_price == 4.995


def test_get_average_entry_price():
    # simple example
    q1 = 100
    p1 = np.float64(10.0)
    q2 = 100
    p2 = np.float64(20.0)
    assert get_average_entry_price(p1, p2, q1, q2) == 15.0
    # more complicated example
    q1 = 10
    p1 = np.float64(10.0)
    q2 = 100
    p2 = np.float64(5.0)
    assert get_average_entry_price(p1, p2, q1, q2).round(2) == 5.45


def test_process_df_calc():
    # no calc
    test_df = get_full_df()
    new_df = process_df(test_df)
    assert_frame_equal(test_df, new_df)

    # calc
    test_df = get_df_input()
    new_df = process_df(test_df)
    assert len(test_df) == len(new_df)
    assert "spread" in new_df
    assert "slippage" in new_df
    assert "midpoint" in new_df


def test_process_df_resample():
    test_df = get_full_df()
    # upsample
    new_df = process_df(test_df, "continuous_24_7", "30min")
    assert test_df.shape[1] == new_df.shape[1]
    assert ((2 * test_df.shape[0]) - 1) == new_df.shape[0]
    assert new_df.index.inferred_freq == "30min"
    # downsample
    new_df = process_df(test_df, "continuous_24_7", "D")
    assert test_df.shape[1] == new_df.shape[1]
    assert len(new_df) == 1
    new_series = new_df.iloc[0]
    assert new_series["open"] == 1.0
    assert new_series["high"] == 4.0
    assert new_series["low"] == 1.0
    assert new_series["close"] == 4.0
    assert new_series["volume"] == 400.0
    assert new_series["slippage"] == 0.1
    assert new_series["midpoint"] == 2.5
    assert new_series["spread"] == 0.1


def test_process_df_invalid_calendar():
    test_df = get_df_input()
    with pytest.raises(BacktesterException, match="Unsupported resampling operation"):
        process_df(test_df, cal="exchange_hours", resample_freq="1D")


def test_process_df_invalid_args_sampling():
    test_df = get_df_input()
    with pytest.raises(
        BacktesterException, match="Must provide both 'cal' and 'resample_freq' to resample"
    ):
        process_df(test_df, cal="exchange_hours")
    with pytest.raises(
        BacktesterException, match="Must provide both 'cal' and 'resample_freq' to resample"
    ):
        process_df(test_df, resample_freq="test")
