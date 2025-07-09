from typing import Literal, NamedTuple
from pandas import DataFrame, Timestamp
from numpy import float64

OrderType = Literal["buy", "sell"]
OrderStatus = Literal["filled", "rejected", "unsupported"]
MarketData = dict[str, DataFrame]


class Order(NamedTuple):
    ticker: str
    type: OrderType
    quantity: int
    limit_price: float | None = None


class ExecutedOrder(NamedTuple):  # TODO: add id
    time: Timestamp
    ticker: str
    type: OrderType
    quantity: int
    price: float64
    status: OrderStatus


class Position(NamedTuple):
    time: Timestamp = Timestamp.min
    quantity: int = 0
    entry_price: float64 = float64(0)
    fill_price: float64 = float64(0)
    unrealised_pnl: float64 = float64(0)
    realised_pnl: float64 = float64(0)
