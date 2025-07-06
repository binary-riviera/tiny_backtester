from typing import Literal, NamedTuple
from pandas import DataFrame

OrderType = Literal["buy", "sell"]
OrderStatus = Literal["filled", "rejected", "unsupported"]
MarketData = dict[str, DataFrame]


class Order(NamedTuple):
    ticker: str
    type: OrderType
    quantity: int
    limit_price: float | None = None


class ExecutedOrder(NamedTuple):  # TODO: add id
    ticker: str
    type: OrderType
    quantity: int
    price: float
    status: OrderStatus
