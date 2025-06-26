from typing import Optional
from .strategy import Strategy
from .backtester_exception import BacktesterException
from .backtester_types import MarketData, ExecutedOrder, Order, OrderStatus, OrderType
from .dataloader import load_csv


class Engine:
    market_data: MarketData = {}

    def load_timeseries(self, filepath: str, ticker: Optional[str] = None):
        if not filepath:
            raise BacktesterException("must provide filepath")
        ticker, data = load_csv(filepath, ticker)
        self.market_data[ticker] = data

    def run(self, strategy: Strategy, n_epochs: int = 1000000):
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
        n_epochs = min(
            *[len(self.market_data[ticker]) for ticker in strategy.tickers], n_epochs
        )
        for i in range(n_epochs + 1):
            cur_data = {
                ticker: self.market_data[ticker].iloc[:i] for ticker in strategy.tickers
            }
            if orders := strategy.run(cur_data):
                self.execute_orders(strategy, orders, cur_data)

    def execute_orders(
        self, strategy: Strategy, orders: list[Order], cur_data: MarketData
    ) -> list[ExecutedOrder]:
        return [self.execute_order(strategy, order, cur_data) for order in orders]

    def execute_order(
        self, strategy: Strategy, order: Order, cur_data: MarketData
    ) -> ExecutedOrder:
        price = cur_data[order.ticker].iloc[-1].values[0]

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
