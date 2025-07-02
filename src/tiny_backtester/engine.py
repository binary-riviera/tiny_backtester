from typing import Optional
import pandas as pd
import numpy as np
from numpy.typing import ArrayLike

from tiny_backtester.data_utils import load_timeseries
from .strategy import Strategy
from .backtester_exception import BacktesterException
from .backtester_types import MarketData, ExecutedOrder, Order, OrderStatus, OrderType


class Engine:
    # pricing parameters
    k: float = 0.5  # slippage sensitivity constant
    # class variables
    market_data: MarketData = {}

    def load_timeseries(self, filepath: str, ticker: Optional[str] = None):
        ticker, data = load_timeseries(filepath, ticker)
        self.market_data[ticker] = data

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
        strategy.preload(self.market_data)
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
        price = self.get_execution_price(order, cur_data[order.ticker])

        def make_executed_order(status: OrderStatus) -> ExecutedOrder:
            return ExecutedOrder(
                strategy.label, order.ticker, order.type, order.quantity, price, status
            )

        total_order_price = price * order.quantity
        match order.type:
            case OrderType.BUY:
                if total_order_price > strategy.funds:
                    return make_executed_order(OrderStatus.REJECTED)
                strategy.funds -= total_order_price
                strategy.portfolio[order.ticker] += order.quantity
                return make_executed_order(OrderStatus.FILLED)
            case OrderType.SELL:
                if strategy.portfolio[order.ticker] < order.quantity:
                    return make_executed_order(OrderStatus.REJECTED)
                strategy.funds += total_order_price
                strategy.portfolio[order.ticker] -= order.quantity
                return make_executed_order(OrderStatus.FILLED)
            case _:
                return make_executed_order(OrderStatus.UNSUPPORTED)

    def get_execution_price(self, order: Order, timeseries: pd.DataFrame) -> np.float64:
        latest = timeseries.iloc[-1]
        midpoint = (latest["high"] + latest["low"]) / 2
        half_bid_ask_spread = self.get_bid_ask_spread(timeseries["close"]) / 2
        # TODO: above can all be precalculated and converted into numpy arrays for speed
        slippage_pct = self.k * (order.quantity / timeseries["volume"].iloc[-1])
        match order.type:
            case OrderType.BUY:
                return np.float64((midpoint + half_bid_ask_spread) * (1 + slippage_pct))
            case OrderType.SELL:
                return np.float64((midpoint - half_bid_ask_spread) * (1 - slippage_pct))

    def get_bid_ask_spread(self, timeseries: ArrayLike) -> np.float64:
        # implementation of "A Simple Implicit Measure of the Effective Bid-Ask Spread in an Efficient Market [1984], Roll"
        # Roll defines the bid ask spread as:
        # Spread = 2√Cov(Δp_t, Δp_t+1)
        # TODO: this can be precalculated
        return np.float64(2 * np.sqrt(np.cov(np.diff(timeseries))))
