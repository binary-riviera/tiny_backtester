from typing import Optional, assert_never
import pandas as pd
import numpy as np
from numpy.typing import ArrayLike
from .strategy import Strategy
from .backtester_exception import BacktesterException
from .backtester_types import MarketData, ExecutedOrder, Order, OrderStatus, OrderType
from .dataloader import load_csv


class Engine:
    # pricing parameters
    k: float = 0.5  # slippage sensitivity constant
    # class variables
    market_data: MarketData = {}

    def load_timeseries_from_csv(self, filepath: str, ticker: Optional[str] = None):
        if not filepath:
            raise BacktesterException("must provide filepath")
        ticker, data = load_csv(filepath, ticker)
        self.market_data[ticker] = data

    def load_timeseries_from_df(self, df: pd.DataFrame, ticker: str):
        # TODO: check this data is correct
        self.market_data[ticker] = df

    def run(self, strategy: Strategy, n_epochs: int | None = None):
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
        print("preloaded data")
        # not sure if this is the best approach, but I'm going to find the shortest timeseries in tickers then just step through that
        min_data_length = min([len(self.market_data[t]) for t in strategy.tickers])
        n_epochs = min_data_length if not n_epochs else min(min_data_length, n_epochs)
        executed_orders: list[ExecutedOrder] = []
        for i in range(n_epochs + 1):
            cur_data = {
                ticker: self.market_data[ticker].iloc[:i] for ticker in strategy.tickers
            }
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
        midpoint = (timeseries["high"].iloc[-1] + timeseries["low"].iloc[-1]) / 2
        print(midpoint)
        half_bid_ask_spread = self.get_bid_ask_spread(timeseries["close"]) / 2
        print(half_bid_ask_spread)
        slippage_pct = self.k * (order.quantity / timeseries["volume"].iloc[-1])
        print(slippage_pct)
        match order.type:
            case OrderType.BUY | OrderType.BUY_LIMIT:
                print("buy")
                return (midpoint + half_bid_ask_spread) * (1 + slippage_pct)
            case OrderType.SELL | OrderType.SELL_LIMIT:
                print("sell")
                return (midpoint - half_bid_ask_spread) * (1 - slippage_pct)

    def get_bid_ask_spread(self, timeseries: ArrayLike) -> np.float64:
        # implementation of "A Simple Implicit Measure of the Effective Bid-Ask Spread in an Efficient Market [1984], Roll"
        # Roll defines the bid ask spread as:
        # Spread = 2√Cov(Δp_t, Δp_t+1)
        # TODO: this can be precalculated
        return np.float64(2 * np.sqrt(np.cov(np.diff(timeseries))))
