from enum import Enum, auto
from typing import NamedTuple
from pandas import DataFrame


class OrderType(Enum):
    BUY = auto()
    SELL = auto()


class OrderStatus(Enum):
    FILLED = auto()
    REJECTED = auto()


class Order(NamedTuple):
    ticker: str
    order_type: OrderType
    quantity: int


class ExecutedOrder(NamedTuple):
    strategy_id: str
    order_type: OrderType
    quantity: int
    price: float
    status: OrderStatus


Datasets = dict[str, DataFrame]
