from typing import Literal, NamedTuple, TypedDict, Optional
from numpy import float64
import pandas as pd
import pandera.pandas as pa
import pandera.typing.pandas as pat

OrderType = Literal["buy", "sell"]
OrderStatus = Literal["filled", "rejected", "unsupported"]
MarketData = dict[str, pd.DataFrame]
RunResults = TypedDict("RunResults", {"orders": pd.DataFrame, "positions": dict[str, pd.DataFrame]})


class Order(NamedTuple):
    ticker: str
    type: OrderType
    quantity: int
    limit_price: float | None = None


class ExecutedOrder(NamedTuple):
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


class TimeSeries(pa.DataFrameModel):
    datetime: pat.Index[pd.Timestamp]
    open: pat.Series[float]
    high: pat.Series[float]
    low: pat.Series[float]
    close: pat.Series[float]
    volume: Optional[pat.Series[int]]
    midpoint: Optional[pat.Series[float]]
    slippage: Optional[pat.Series[float]]
    spread: Optional[pat.Series[float]]
