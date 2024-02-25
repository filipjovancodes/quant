import asyncio
from ib_insync import IB, LimitOrder, Option, Stock, util


class TradeData:
    def __init__(
        self,
        symbol,
        exchange,
        currency,
        multiplier,
        expiry,
        strike,
        right,
        option_start,
        quantity,
        bound_percent,
        max_cents_plus_base,
    ):
        self.symbol = symbol
        self.exchange = exchange
        self.currency = currency
        self.multiplier = multiplier
        self.expiry = expiry
        self.strike = strike
        self.right = right
        self.option_start = option_start
        self.quantity = quantity
        self.bound_percent = bound_percent
        self.max_cents_plus_base = max_cents_plus_base


class TradeManager:
    # TODO exit all trades on shut down
    # TODO think through way to add trades while running

    async def run_trades(self, trades):
        ib = IB()
        util.startLoop()
        await ib.connectAsync(
            "127.0.0.1", 7496, clientId=1, readonly=True
        )  # Connect to IBKR TWS or IB Gateway

        # Execute async functions concurrently
        await asyncio.gather(*trades)

        ib.disconnect()

    def run(self, trades):
        util.run(self.run_trades(trades))

    # async def start_trade_covered_call(self, symbol, exchange, currency, multiplier, expiry, strike, option_start, quantity, bound_percent, max_cents_plus_base):
    #     # improve this code and test it
    #     # make it so code for executing trade is reusable for calls, puts, and stocks
    #     # should be market making buying puts for all active positions at all times
    #     # could use ask and bid size to determine when we're actually market making -> when we're top order

    #     stock_contract = Stock(symbol, exchange, currency)
    #     option_contract = Option(
    #         symbol, expiry, strike, "C", exchange, multiplier, currency
    #     )
    #     stock_start = await self.get_stock_price(symbol)

    #     self._buy_covered_call(
    #         stock_contract,
    #         option_contract,
    #         stock_start,
    #         option_start,
    #         quantity,
    #         bound_percent,
    #         max_cents_plus_base,
    #     )

    def start_trade_covered_call(self, trade):
        # improve this code and test it
        # make it so code for executing trade is reusable for calls, puts, and stocks
        # should be market making buying puts for all active positions at all times
        # could use ask and bid size to determine when we're actually market making -> when we're top order

        stock_contract = Stock(
            trade.symbol,
            trade.exchange,
            trade.currency,
        )

        option_contract = Option(
            trade.symbol,
            trade.expiry,
            trade.strike,
            trade.right,
            trade.exchange,
            trade.multiplier,
            trade.currency,
        )

        stock_start = self.get_stock_price(trade.symbol)

        self.pm.buy_covered_call(
            stock_contract,
            option_contract,
            stock_start,
            trade.option_start,
            trade.quantity,
            trade.bound_percent,
            trade.max_cents_plus_base,
        )

    def start_trade_put(self, trade):
        # put does not need to price adjust because it is out of the money
        # just manage entry and exit
        # automate price entry at risk free rate

        option_contract = Option(
            trade.symbol,
            trade.expiry,
            trade.strike,
            trade.right,
            trade.exchange,
            trade.multiplier,
            trade.currency,
        )

        self._buy_put(
            option_contract,
            trade.option_start,
            trade.quantity,
        )

    def _buy_put(self, option_contract, option_start, quantity):
        trade = self.create_limit_trade(option_contract, "Buy", quantity, option_start)

        while trade.orderStatus.status != "Submitted":
            print("Waiting trade status to be Submitted")
            self.sleep(1)

        while trade.orderStatus.status == "Submitted":
            print("Last put status ", trade.orderStatus.status)
            self.sleep(1)

    async def _buy_covered_call_async(
        self,
        stock_contract,
        option_contract,
        stock_start,
        option_start,
        quantity,
        bound_percent,
        max_cents_plus_base,
    ):
        # Submit the initial limit order to sell the option
        trade = self.create_limit_trade(option_contract, "Sell", quantity, option_start)
        lower_bound = stock_start * (1 - bound_percent)
        upper_bound = stock_start * (1 + bound_percent)

        while trade.orderStatus.status != "Submitted":
            print("Waiting trade status to be Submitted")
            self.sleep(1)

        option_price = option_start
        old_stock_price = stock_start
        while trade.orderStatus.status == "Submitted":
            new_stock_price = await self.get_stock_price_async(option_contract.symbol)
            print("Last stock price ", new_stock_price)

            if new_stock_price < lower_bound or new_stock_price > upper_bound:
                self.cancel_trade(trade)
                break

            if new_stock_price != old_stock_price:
                option_price += new_stock_price - old_stock_price
                print("Last option price ", option_price)
                self.modify_limit_trade_price(trade, option_price)

            old_stock_price = new_stock_price
            self.sleep(1)

        if trade.orderStatus.status == "Filled":
            self._buy_stock_fast_async(
                stock_contract, quantity * 100, max_cents_plus_base
            )

    async def _buy_stock_fast_async(
        self, stock_contract, quantity, max_cents_plus_base
    ):
        price = self.get_stock_price(stock_contract.symbol)
        trade = self.create_limit_trade(stock_contract, "Buy", quantity, price)
        self.sleep(1)

        if trade.orderStatus.status == "Filled":
            return

        while trade.orderStatus.status != "Submitted":
            print("Waiting trade status to be Submitted")
            self.sleep(1)

        while trade.orderStatus.status == "Submitted":
            new_stock_price = await self.get_stock_price_async(stock_contract.symbol)

            for i in range(max_cents_plus_base):
                trade = self.modify_limit_trade_price(
                    trade, new_stock_price + (i * 0.01)
                )
                self.sleep(1)

                if trade.order.status != "Submitted":
                    return

    def _buy_covered_call(
        self,
        stock_contract,
        option_contract,
        stock_start,
        option_start,
        quantity,
        bound_percent,
        max_cents_plus_base,
    ):
        # Submit the initial limit order to sell the option
        trade = self.create_limit_trade(option_contract, "Sell", quantity, option_start)
        lower_bound = stock_start * (1 - bound_percent)
        upper_bound = stock_start * (1 + bound_percent)

        while trade.orderStatus.status != "Submitted":
            print("Waiting trade status to be Submitted")
            self.sleep(1)

        option_price = option_start
        old_stock_price = stock_start
        while trade.orderStatus.status == "Submitted":
            new_stock_price = self.get_stock_price(option_contract.symbol)
            print("Last stock price ", new_stock_price)

            if new_stock_price < lower_bound or new_stock_price > upper_bound:
                self.cancel_trade(trade)
                break

            if new_stock_price != old_stock_price:
                option_price += new_stock_price - old_stock_price
                print("Last option price ", option_price)
                self.modify_limit_trade_price(trade, option_price)

            old_stock_price = new_stock_price
            self.sleep(1)

        if trade.orderStatus.status == "Filled":
            self._buy_stock_fast(stock_contract, quantity * 100, max_cents_plus_base)

    def _buy_stock_fast(self, stock_contract, quantity, max_cents_plus_base):
        price = self.get_stock_price(stock_contract.symbol)
        trade = self.create_limit_trade(stock_contract, "Buy", quantity, price)
        self.sleep(1)

        if trade.orderStatus.status == "Filled":
            return

        while trade.orderStatus.status != "Submitted":
            print("Waiting trade status to be Submitted")
            self.sleep(1)

        while trade.orderStatus.status == "Submitted":
            new_stock_price = self.get_stock_price(stock_contract.symbol)

            for i in range(max_cents_plus_base):
                trade = self.modify_limit_trade_price(
                    trade, new_stock_price + (i * 0.01)
                )
                self.sleep(1)

                if trade.order.status != "Submitted":
                    return

    def create_limit_trade(self, contract, type, quantity, price):
        # Define order parameters
        limitOrder = LimitOrder(
            type, quantity, price, account="U5732481"
        )  # Buying 100 shares of AAPL at a limit price of $150.00

        # Submit the order
        try:
            trade = self.ib.placeOrder(contract, limitOrder)
            print(trade)
            print(f"Order submitted successfully. Order ID: {trade.order.orderId}")
            return trade
        except Exception as e:
            print(f"Error submitting order: {e}")

    def cancel_trade(self, trade):
        try:
            self.ib.cancelOrder(trade.order)
            print(f"Order {trade.order.orderId} canceled successfully.")
        except Exception as e:
            print(f"Error canceling order: {e}")

    def modify_limit_trade_price(self, trade, new_price):
        trade.order.lmtPrice = new_price
        self.ib.placeOrder(trade.contract, trade.order)

    def sleep(self, seconds):
        self.ib.sleep(seconds)
