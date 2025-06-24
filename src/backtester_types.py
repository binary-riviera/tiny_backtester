from enum import Enum, auto
from typing import NamedTuple
from pandas import DataFrame


class OrderType(Enum):
    BUY = auto()
    SELL = auto()


class Order(NamedTuple):
    ticker: str
    order_type: OrderType
    quantity: int


Dataset = dict[str, DataFrame]
