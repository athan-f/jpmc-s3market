import re
import time
from abc import ABC, abstractmethod
from enum import Enum


class TradeIndicator(Enum):
    BUY = 1
    SELL = 2


class Trade:
    def __init__(self, trade_id, stock_name, quantity, indicator: TradeIndicator, traded_price, timestamp):
        self.trade_id = trade_id
        self.stock_name = stock_name
        self.quantity = quantity
        self.indicator = indicator
        self.traded_price = traded_price
        self.timestamp = timestamp

    def get_trade_id(self):
        return self.trade_id

    def get_stock_name(self):
        return self.stock_name

    def get_quantity(self):
        return self.quantity

    def get_indicator(self):
        return self.indicator

    def get_traded_price(self):
        return self.traded_price

    def get_timestamp(self):
        return self.timestamp


class Stock(ABC):
    def __init__(self, name, price):
        if not Stock.is_valid_name(name):
            raise ValueError(f"Invalid stock name: {name}")

        if not Stock.is_valid_price(name, price):
            raise ValueError(f"{name}: Invalid price: {price}")

        self.name = name
        self.price = price
        self.trades = []

    def set_price(self, price):
        if not Stock.is_valid_price(self.name, price):
            raise ValueError(f"{self.name}: Invalid price: {price}")

        self.price = price

    @staticmethod
    def is_valid_name(name):
        return name is not None and re.match("[A-Z]{3}", name)

    @staticmethod
    def is_valid_price(stockName, price):
        # TODO: Add proper validation
        return True

    def add_trade(self, trade: Trade):
        if trade.get_stock_name() != self.name:
            raise ValueError(f"Cannot trade {trade.get_stock_name()} as {self.name}")

        self.set_price(trade.get_traded_price())  # might raise exception

        # append trade only if the price has been set successfully
        self.trades.append(trade)

    @abstractmethod
    def get_dividend_yield(self):
        pass

    def get_volume_weighted_price(self):
        """
        Returns the Volume Weighted Stock Price on the trades in the past 15 minutes, for this Stock object.
        """
        # using 10 seconds instead of 15 minutes to facilitate demonstration
        now_minus_10_seconds = time.time() - 10
        nominator = 0.0
        denominator = 0.0

        for t in reversed(self.trades):
            if t.get_timestamp() < now_minus_10_seconds:
                break
            nominator += t.get_traded_price() * t.get_quantity()
            denominator += t.get_quantity()

        return nominator / denominator if denominator != 0.0 else 0.0

    def is_common(self):
        return isinstance(self, CommonStock)

    def is_preferred(self):
        return isinstance(self, PreferredStock)

    def __lt__(self, other):
        return self.name < other.name

    def __str__(self):
        return f"{self.name}: {self.get_dividend_yield()}"


class CommonStock(Stock):
    def __init__(self, name, last_dividend, price):
        super().__init__(name, price)

        self.last_dividend = last_dividend

    def set_last_dividend(self, last_dividend):
        self.last_dividend = last_dividend

    def get_dividend_yield(self):
        return self.last_dividend / self.price if self.price != 0.0 else 0.0

    def __eq__(self, other):
        if self is other:
            return True
        if not isinstance(other, CommonStock):
            return False
        return self.name == other.name


class PreferredStock(Stock):
    def __init__(self, name, fixed_dividend_ratio, par_value, price):
        super().__init__(name, price)

        self.fixed_dividend_ratio = fixed_dividend_ratio
        self.par_value = par_value

    def set_fixed_dividend_ratio(self, fixed_dividend_ratio):
        self.fixed_dividend_ratio = fixed_dividend_ratio

    def set_par_value(self, par_value):
        self.par_value = par_value

    def get_dividend_yield(self):
        return (self.fixed_dividend_ratio * self.par_value) / self.price if self.price != 0.0 else 0.0

    def __eq__(self, other):
        if self is other:
            return True
        if not isinstance(other, PreferredStock):
            return False
        return self.name == other.name


class Market:
    def __init__(self):
        self.stocks_by_name = {}
        self.trade_id_counter = 1

    def register(self, stock):
        if stock.name in self.stocks_by_name:
            raise ValueError(f"Already registered: {stock.name}")

        self.stocks_by_name[stock.name] = stock

    def find(self, name):
        return self.stocks_by_name[name]

    def buy_now(self, stock_name, quantity, price):
        if stock_name not in self.stocks_by_name:
            raise ValueError(f"Stock {stock_name} not found")

        self.stocks_by_name[stock_name].add_trade(
            Trade(self.trade_id_counter, stock_name, quantity, TradeIndicator.BUY, price, time.time())
        )

        # increment only it the above succeeds
        self.trade_id_counter += 1

    def sell_now(self, stock_name, quantity, price):
        if stock_name not in self.stocks_by_name:
            raise ValueError(f"Stock {stock_name} not found")

        self.stocks_by_name[stock_name].add_trade(
            Trade(self.trade_id_counter, stock_name, quantity, TradeIndicator.SELL, price, time.time())
        )

        # increment only it the above succeeds
        self.trade_id_counter += 1

    def update_stock_prices(self, new_prices):
        """
        Updates the prices of multiple stocks.
        :param new_prices: A dictionary where keys are stock names and values are the new prices.
        """
        for stock_name, new_price in new_prices.items():
            if stock_name in self.stocks_by_name:
                self.stocks_by_name[stock_name].set_price(new_price)
            else:
                print(f"Stock '{stock_name}' not found.")

    def get_geometric_mean(self):
        """
        Returns the Geometric Mean of prices for all stocks
        """
        stocks = self.stocks_by_name.values()
        if len(stocks) == 0:
            raise ValueError("Insufficient data")
        product = 1.0
        for s in stocks:
            product *= s.get_price()
        return product ** (1.0 / len(stocks))

    @staticmethod
    def print_sample_dividend_yields():
        print("Dividend yields:")
        print(CommonStock("TEA", 0, 34.42))
        print(PreferredStock("POP", 3.5 / 100, 100, 47.48))
        print(CommonStock("ALE", 23, 24.43))
        print(PreferredStock("GIN", 2.0 / 100, 100, 15.45))
        print(CommonStock("JOE", 13, 33.52))


if __name__ == "__main__":
    Market.print_sample_dividend_yields()

    m = Market()
    m.register(CommonStock("TEA", 0, 34.42))
    m.register(PreferredStock("GIN", 2.0 / 100, 100, 15.45))
    m.buy_now("TEA", 10, 34.30)
    time.sleep(1)
    m.sell_now("TEA", 20, 34.20)

    print("get_volume_weighted_price for TEA")
    print(m.find("TEA").get_volume_weighted_price())
    time.sleep(9)
    print(m.find("TEA").get_volume_weighted_price())
    time.sleep(1)
    print(m.find("TEA").get_volume_weighted_price())
