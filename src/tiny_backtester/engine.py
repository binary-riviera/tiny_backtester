from typing import Optional, Literal
import pandas as pd
import numpy as np

from .data_utils import load_timeseries
from .strategy import Strategy
from .backtester_exception import BacktesterException
from .backtester_types import MarketData, ExecutedOrder, Order, OrderStatus


class Engine:
    # pricing parameters / options
    k: float = 0.5  # slippage sensitivity constant
    spread_type: Literal["fixed", "rolling"] = "fixed"
    # class variables
    market_data: MarketData = {}

    def run(self, strat: Strategy, n_epochs: Optional[int] = None):
        if not strat.funds or strat.funds <= 0:
            raise BacktesterException("strategy funds must be greater than 0")
        if not self.market_data or len(self.market_data) == 0:
            raise BacktesterException("must provide data for backtesting")
        if not strat.tickers or len(strat.tickers) == 0:
            raise BacktesterException("strategy must have tickers to run strategy on")
        if not strat.tickers.issubset(set(self.market_data.keys())):
            raise BacktesterException(
                "data for tickers not found: "
                + str(strat.tickers - set(self.market_data.keys()))
            )
        strat.precalc(self.market_data)
        min_data_length = min([len(self.market_data[t]) for t in strat.tickers])
        n_epochs = min_data_length if not n_epochs else min(min_data_length, n_epochs)
        executed_orders: list[ExecutedOrder] = []
        pos_info = {
            t: self.get_position_df(df, n_epochs)
            for t, df in self.market_data.items()
            if t in strat.tickers
        }
        for i in range(n_epochs + 1):
            cur_data = {t: self.market_data[t].iloc[:i] for t in strat.tickers}
            if orders := strat.run(cur_data):
                executed_orders.extend(
                    self.execute_orders(strat, orders, cur_data, pos_info)
                )

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

    def get_position_df(self, df: pd.DataFrame, n_epochs: int) -> pd.DataFrame:
        pos_df = pd.DataFrame(index=df.iloc[:n_epochs].index)
        pos_df["position_quantity"] = np.nan
        pos_df["entry_price"] = np.nan
        pos_df["fill_price"] = np.nan
        pos_df["realised_pnl"] = np.nan
        pos_df["unrealised_pnl"] = np.nan
        return pos_df

    def execute_orders(
        self,
        strat: Strategy,
        orders: list[Order],
        cur_data: MarketData,
        pos_info: MarketData,
    ) -> list[ExecutedOrder]:
        return [
            self.execute_order(strat, order, cur_data, pos_info) for order in orders
        ]

    def execute_order(
        self,
        strat: Strategy,
        order: Order,
        cur_data: MarketData,
        pos_info: MarketData,
    ) -> ExecutedOrder:
        # TODO: implement limit orders
        price = self.get_execution_price(order, cur_data[order.ticker])

        def make_executed_order(status: OrderStatus) -> ExecutedOrder:
            return ExecutedOrder(
                order.ticker, order.type, order.quantity, price, status
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

    @staticmethod
    def get_execution_price(order: Order, ts: pd.DataFrame) -> np.float64:
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

    @staticmethod
    def get_average_entry_price(
        p1: np.float64, p2: np.float64, q1: int, q2: int
    ) -> np.float64:
        return (p1 * q1 + p2 * q2) / (q1 + q2)
