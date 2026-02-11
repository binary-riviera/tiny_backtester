from typing import Optional
import pandas as pd
import numpy as np
import pandera.pandas as pa
import pandera.typing as pat

from tiny_backtester.strategy import Strategy
from tiny_backtester.utils.backtester_exception import BacktesterException
from tiny_backtester.utils.backtester_types import (
    MarketData,
    ExecutedOrder,
    Order,
    OrderStatus,
    Position,
    RunResults,
    TimeSeries,
)
from tiny_backtester.utils.math_utils import (
    get_average_entry_price,
    get_execution_price,
    process_df,
)


class Engine:

    def __init__(self):
        self.market_data: MarketData = {}

    def run(self, strat: Strategy, n_epochs: Optional[int] = None) -> RunResults:
        if not strat.funds or strat.funds <= 0:
            raise BacktesterException("strategy funds must be greater than 0")
        if not self.market_data or len(self.market_data) == 0:
            raise BacktesterException("must provide data for backtesting")
        if not strat.tickers or len(strat.tickers) == 0:
            raise BacktesterException("strategy must have tickers to run strategy on")
        if not strat.tickers.issubset(set(self.market_data.keys())):
            raise BacktesterException(
                "data for tickers not found: " + str(strat.tickers - set(self.market_data.keys()))
            )
        strat.precalc(self.market_data)
        min_data_length = min(len(self.market_data[t]) for t in strat.tickers)
        n_epochs = min_data_length if not n_epochs else min(min_data_length, n_epochs)
        order_log: list[ExecutedOrder] = []
        pos_info = {t: [Position()] for t in strat.tickers}
        for i in range(1, n_epochs + 1):
            cur_data = {t: self.market_data[t].iloc[:i] for t in strat.tickers}
            executed_orders = self.execute_orders(strat, strat.run(cur_data) or [], cur_data)
            for o in executed_orders:
                if o.status == "filled":
                    pos_info[o.ticker].append(
                        self.get_position(pos_info[o.ticker][-1], o, cur_data[o.ticker].iloc[-1])
                    )
            order_log.extend(executed_orders)

        return {
            "orders": pd.DataFrame(data=order_log),
            "positions": {t: pd.DataFrame(data=d) for t, d in pos_info.items()},
        }

    @pa.check_types
    def load_ts(self, ticker: str, df: pat.DataFrame[TimeSeries]):
        self.market_data[ticker] = process_df(df)

    @classmethod
    def execute_orders(
        cls, strat: Strategy, orders: list[Order], cur_data: MarketData
    ) -> list[ExecutedOrder]:
        return [cls.execute_order(strat, order, cur_data) for order in orders]

    @classmethod
    def execute_order(cls, strat: Strategy, order: Order, cur_data: MarketData) -> ExecutedOrder:
        latest = cur_data[order.ticker].iloc[-1]
        price = get_execution_price(order.type, latest)

        def make_executed_order(status: OrderStatus) -> ExecutedOrder:
            return ExecutedOrder(
                latest.name,
                order.ticker,
                order.type,
                order.quantity,
                price,
                status,
            )

        total_order_price = price * order.quantity
        if order.type == "buy":
            if total_order_price > strat.funds or (order.limit_price and order.limit_price < price):
                return make_executed_order("rejected")
            strat.funds -= total_order_price
            strat.portfolio[order.ticker] += order.quantity
            return make_executed_order("filled")
        elif order.type == "sell":
            if strat.portfolio[order.ticker] < order.quantity or (
                order.limit_price and order.limit_price > price
            ):
                return make_executed_order("rejected")
            strat.funds += total_order_price
            strat.portfolio[order.ticker] -= order.quantity
            return make_executed_order("filled")
        return make_executed_order("unsupported")

    @classmethod
    def get_position(cls, last_pos: Position, order: ExecutedOrder, latest: pd.Series) -> Position:
        quantity_change = order.quantity if order.type == "buy" else -order.quantity
        quantity = last_pos.quantity + quantity_change
        entry_price = np.float64(0)
        realised_pnl = np.float64(last_pos.realised_pnl)
        unrealised_pnl = quantity * get_execution_price("sell", latest)
        if order.type == "buy":
            entry_price = get_average_entry_price(
                last_pos.entry_price, order.price, last_pos.quantity, order.quantity
            )
        elif order.type == "sell":
            entry_price = np.float64(0) if quantity == 0 else last_pos.entry_price
            realised_pnl += (order.price - last_pos.entry_price) * order.quantity

        return Position(
            order.time,
            quantity,
            entry_price,
            order.price,
            unrealised_pnl,
            realised_pnl,
        )
