from typing import Optional, Literal
import pandas as pd
import numpy as np

from .data_utils import load_timeseries
from .strategy import Strategy
from .backtester_exception import BacktesterException
from .backtester_types import (
    MarketData,
    ExecutedOrder,
    Order,
    OrderStatus,
    OrderType,
    Position,
)


class Engine:
    # pricing parameters / options
    k: float = 0.5  # slippage sensitivity constant
    spread_type: Literal["fixed", "rolling"] = "fixed"
    # class variables
    market_data: MarketData = {}

    def run(self, strat: Strategy, n_epochs: Optional[int] = None) -> dict:
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
        min_data_length = min([len(self.market_data[t]) for t in strat.tickers])
        n_epochs = min_data_length if not n_epochs else min(min_data_length, n_epochs)
        executed_orders: list[ExecutedOrder] = []
        pos_info = {t: [Position()] for t in strat.tickers}
        for i in range(1, n_epochs + 1):
            cur_data = {t: self.market_data[t].iloc[:i] for t in strat.tickers}
            if orders := strat.run(cur_data):
                orders = self.execute_orders(strat, orders, cur_data)
                for o in orders:
                    if o.status == "filled":
                        pos_info[o.ticker].append(
                            self.get_position(
                                pos_info[o.ticker][-1], o, cur_data[o.ticker].iloc[-1]
                            )
                        )
                executed_orders.extend(orders)

        return {
            "orders": pd.DataFrame(data=executed_orders),
            "positions": {t: pd.DataFrame(data=d) for t, d in pos_info.items()},
        }

    def load_timeseries(self, filepath: str, ticker: Optional[str] = None):
        ticker, df = load_timeseries(filepath, ticker)
        # precalculate data needed for pricing
        # TODO: future speed up: store calcs in numpy array associated with ticker instead of df
        df["midpoint"] = (df["high"] + df["low"]) / 2
        df["slippage"] = self.k / df["volume"]
        if self.spread_type == "fixed":
            # implementation of "A Simple Implicit Measure of the Effective Bid-Ask Spread in an Efficient Market [1984], Roll"
            delta = np.diff(df["close"].to_numpy())
            cov = np.cov(delta)
            spread = 2 * np.sqrt(-cov) if cov < 0 else 0.0
            df["spread"] = spread
            # TODO: store spread as seperate attribute in market_data
        self.market_data[ticker] = df

    @classmethod
    def execute_orders(
        cls,
        strat: Strategy,
        orders: list[Order],
        cur_data: MarketData,
    ) -> list[ExecutedOrder]:
        return [cls.execute_order(strat, order, cur_data) for order in orders]

    @classmethod
    def execute_order(
        cls,
        strat: Strategy,
        order: Order,
        cur_data: MarketData,
    ) -> ExecutedOrder:
        # TODO: implement limit orders
        latest = cur_data[order.ticker].iloc[-1]
        price = cls.get_execution_price(order.quantity, order.type, latest)

        def make_executed_order(status: OrderStatus) -> ExecutedOrder:
            return ExecutedOrder(
                latest.index, order.ticker, order.type, order.quantity, price, status  # type: ignore
            )

        total_order_price = price * order.quantity
        if order.type == "buy":
            if total_order_price > strat.funds:
                return make_executed_order("rejected")
            strat.funds -= total_order_price
            strat.portfolio[order.ticker] += order.quantity
            return make_executed_order("filled")
        elif order.type == "sell":
            if strat.portfolio[order.ticker] < order.quantity:
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
        unrealised_pnl = cls.get_execution_price(quantity, "sell", latest)
        if order.type == "buy":
            entry_price = cls.get_average_entry_price(
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

    @staticmethod
    def get_execution_price(quantity: int, type: OrderType, row: pd.Series) -> np.float64:
        slippage_pct = quantity * row["slippage"]
        if type == "buy":
            return np.float64((row["midpoint"] + 0.5 * row["spread"]) * (1 + slippage_pct))
        elif type == "sell":
            return np.float64((row["midpoint"] + 0.5 * row["spread"]) * (1 - slippage_pct))
        return np.float64(np.nan)  # FIXME: why do I need to cast this????

    @staticmethod
    def get_average_entry_price(p1: np.float64, p2: np.float64, q1: int, q2: int) -> np.float64:
        return (p1 * q1 + p2 * q2) / (q1 + q2)
