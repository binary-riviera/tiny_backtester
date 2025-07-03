from typing import Literal, NamedTuple
from pandas import DataFrame

OrderType = Literal["buy", "sell"]

OrderStatus = Literal["filled", "rejected", "unsupported"]


class Order(NamedTuple):
    ticker: str
    type: OrderType
    quantity: int
    limit_price: float | None = None


class ExecutedOrder(NamedTuple):
    strategy_id: str
    ticker: str
    type: OrderType
    quantity: int
    price: float
    status: OrderStatus


MarketData = dict[str, DataFrame]
