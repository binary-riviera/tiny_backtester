from typing import Optional, Literal
import pandas as pd
import numpy as np
from numpy.typing import ArrayLike

from tiny_backtester.data_utils import load_timeseries
from .strategy import Strategy
from .backtester_exception import BacktesterException
from .backtester_types import MarketData, ExecutedOrder, Order, OrderStatus, OrderType


class Engine:
    # pricing parameters / options
    k: float = 0.5  # slippage sensitivity constant
    spread_type: Literal["fixed", "rolling"] = (
        "fixed"  # fixed or rolling spread calculations
    )
    # class variables
    market_data: MarketData = {}

    def load_timeseries(self, filepath: str, ticker: Optional[str] = None):
        ticker, data = load_timeseries(filepath, ticker)
        self.market_data[ticker] = data

    def precalc(self):
        """precalculate data needed for pricing"""
        for df in self.market_data.values():
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
            elif self.spread_type == "rolling":
                raise BacktesterException(
                    "rolling spread calculation not implemented yet"
                )

    def run(self, strategy: Strategy, n_epochs: Optional[int] = None):
        if not strategy.funds or strategy.funds <= 0:
            raise BacktesterException("strategy funds must be greater than 0")
        if not self.market_data or len(self.market_data) == 0:
            raise BacktesterException("must provide data for backtesting")
        if not strategy.tickers or len(strategy.tickers) == 0:
            raise BacktesterException("strategy must have tickers to run strategy on")
        if not strategy.tickers.issubset(set(self.market_data.keys())):
            raise BacktesterException(
                "data for tickers not found: "
                + str(strategy.tickers - set(self.market_data.keys()))
            )
        self.precalc()
        strategy.precalc(self.market_data)
        min_data_length = min([len(self.market_data[t]) for t in strategy.tickers])
        n_epochs = min_data_length if not n_epochs else min(min_data_length, n_epochs)
        executed_orders: list[ExecutedOrder] = []
        for i in range(n_epochs + 1):
            cur_data = {t: self.market_data[t].iloc[:i] for t in strategy.tickers}
            if orders := strategy.run(cur_data):
                executed_orders.extend(self.execute_orders(strategy, orders, cur_data))

        return {"executed_orders": pd.DataFrame(executed_orders)}

    def execute_orders(
        self, strategy: Strategy, orders: list[Order], cur_data: MarketData
    ) -> list[ExecutedOrder]:
        return [self.execute_order(strategy, order, cur_data) for order in orders]

    def execute_order(
        self, strategy: Strategy, order: Order, cur_data: MarketData
    ) -> ExecutedOrder:
        # TODO: implement limit orders
        price = self.get_execution_price(order, cur_data[order.ticker])

        def make_executed_order(status: OrderStatus) -> ExecutedOrder:
            return ExecutedOrder(
                order.ticker, order.type, order.quantity, price, status
            )

        total_order_price = price * order.quantity
        if order.type == "buy":
            if total_order_price > strategy.funds:
                return make_executed_order("rejected")
            strategy.funds -= total_order_price
            strategy.portfolio[order.ticker] += order.quantity
            return make_executed_order("filled")
        elif order.type == "sell":
            if strategy.portfolio[order.ticker] < order.quantity:
                return make_executed_order("rejected")
            strategy.funds += total_order_price
            strategy.portfolio[order.ticker] -= order.quantity
            return make_executed_order("filled")
        return make_executed_order("unsupported")

    def get_execution_price(self, order: Order, ts: pd.DataFrame) -> np.float64:
        latest = ts.iloc[-1]
        slippage_pct = order.quantity * latest["slippage"]
        if order.type == "buy":
            return np.float64(
                (latest["midpoint"] + 0.5 * latest["spread"]) * (1 + slippage_pct)
            )
        elif order.type == "sell":
            return np.float64(
                (latest["midpoint"] + 0.5 * latest["spread"]) * (1 - slippage_pct)
            )
        return np.float64(np.nan)  # why do I need to cast this????
