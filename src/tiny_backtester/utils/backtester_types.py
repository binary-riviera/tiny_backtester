from typing import Literal, NamedTuple, TypedDict
from numpy import float64
from functools import partial
import pandas as pd
import pandera.pandas as pa

OrderType = Literal["buy", "sell"]
OrderStatus = Literal["filled", "rejected", "unsupported"]
MarketData = dict[str, pd.DataFrame]
RunResults = TypedDict("RunResults", {"orders": pd.DataFrame, "positions": dict[str, pd.DataFrame]})


class Order(NamedTuple):
    ticker: str
    type: OrderType
    quantity: int
    limit_price: float | None = None


class ExecutedOrder(NamedTuple):  # TODO: add id
    time: pd.Timestamp
    ticker: str
    type: OrderType
    quantity: int
    price: float64
    status: OrderStatus


class Position(NamedTuple):
    time: pd.Timestamp = pd.Timestamp.min
    quantity: int = 0
    entry_price: float64 = float64(0)
    fill_price: float64 = float64(0)
    unrealised_pnl: float64 = float64(0)
    realised_pnl: float64 = float64(0)


class Dataset(pa.DataFrameModel):
    idx: pd.DatetimeIndex
    open: pd.Series[float] = pa.Field(gt=0, coerce=True)
    high: pd.Series[float] = pa.Field(gt=0, coerce=True)
    low: pd.Series[float] = pa.Field(gt=0, coerce=True)
    close: pd.Series[float] = pa.Field(gt=0, coerce=True)
    volume: pd.Series[int] = pa.Field(gt=0, coerce=True)


class PrecalcDataset(Dataset):
    midpoint: pd.Series[float] = pa.Field(gt=0, coerce=True)
    slippage: pd.Series[float] = pa.Field(gt=0, coerce=True)
    spread: pd.Series[float] = pa.Field(gt=0, coerce=True)
