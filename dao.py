import asyncio
import csv
from ctypes import util
import sqlite3
import threading
from ib_insync import IB, Contract, Future, LimitOrder, Option, Position, Stock
import jsonpickle

import yfinance

from local_objects import (
    CashStrategyObject,
    CoveredCallStrategy,
    CoveredCallStrategyObject,
    CurrencyHedgeStrategy,
    CurrencyHedgeStrategyObject,
    LongStockStrategy,
    LongStockStrategyObject,
    OptionChainMultipleObject,
    OptionData,
    PositionData,
    PutHedgeStrategyObject,
    StockData,
)
from datetime import datetime
import utils.utils as utils
import pytz


class StrategyBuilder:
    def __init__(self, positions):
        local_positions = self.get_local_positions(positions)
        self.strategy_map = self.map_strategies(local_positions)

    def get_local_positions(self, positions):
        local_positions = {}
        for position in positions:
            identifier = str(position.contract.conId)
            if identifier in local_positions:
                local_positions[identifier].position += position.position
            else:
                local_positions[identifier] = PositionData(
                    contract=position.contract,
                    position=position.position,
                    avgCost=position.avgCost,
                )
        return [position for _, position in local_positions.items()]

    def map_strategies(self, local_positions):
        strategies = {}
        for position in local_positions:
            symbol = position.contract.symbol

            if position.contract.symbol not in strategies:
                strategies[symbol] = {}

            if isinstance(position.contract, Stock):
                if "Stock" in strategies[symbol]:
                    strategies[symbol]["Stock"].append(position)
                else:
                    strategies[symbol]["Stock"] = [position]

            elif (
                isinstance(position.contract, Option) and position.contract.right == "C"
            ):
                if "Call" in strategies[symbol]:
                    strategies[symbol]["Call"].append(position)
                else:
                    strategies[symbol]["Call"] = [position]

            elif (
                isinstance(position.contract, Option) and position.contract.right == "P"
            ):
                if "Put" in strategies[symbol]:
                    strategies[symbol]["Put"].append(position)
                else:
                    strategies[symbol]["Put"] = [position]

            elif isinstance(position.contract, Future):
                if "Future" in strategies[symbol]:
                    strategies[symbol]["Future"].append(position)
                else:
                    strategies[symbol]["Future"] = [position]

            else:
                print("No type specified for instance ", type(position.contract))

        return strategies

    def strategies_to_db(self):
        db_strategies = []

        for symbol, strategy in self.strategy_map.items():

            if "Stock" in strategy and "Call" in strategy and "Put" in strategy:
                stock_position = strategy["Stock"][0]
                call_positions = strategy["Call"]
                put_position = strategy["Put"][0]

                strategy_object = PutHedgeStrategyObject(put_position)
                db_strategies.append(strategy_object)

                for call_position in call_positions:
                    stock = PositionData(
                        contract=stock_position.contract,
                        position=call_position.position * -100,
                        avgCost=stock_position.avgCost,
                    )

                    strategy_object = CoveredCallStrategyObject(
                        stock, call_position
                    )
                    db_strategies.append(strategy_object)

            elif "Stock" in strategy and "Call" in strategy:
                stock_position = strategy["Stock"][0]
                call_positions = strategy["Call"]

                for call_position in call_positions:
                    stock = PositionData(
                        contract=stock_position.contract,
                        position=call_position.position * -100,
                        avgCost=stock_position.avgCost,
                    )
                    strategy_object = CoveredCallStrategyObject(
                        stock, call_position
                    )
                    db_strategies.append(strategy_object)

            elif "Put" in strategy:
                put_position = strategy["Put"][0]
                strategy_object = PutHedgeStrategyObject(put_position)
                db_strategies.append(strategy_object)

            elif "Stock" in strategy:
                stock_position = strategy["Stock"][0]
                strategy_object = LongStockStrategyObject(stock_position)
                db_strategies.append(strategy_object)

            elif "Future" in strategy:
                future_position = strategy["Future"][0]
                strategy_object = CurrencyHedgeStrategyObject(future_position)
                db_strategies.append(strategy_object)

        values = []
        for i, db_strategy in enumerate(db_strategies):
            values.append([i, symbol, jsonpickle.encode(db_strategy)])

        return values


class DAO:
    def __init__(self):
        self.conn = sqlite3.connect("main.db")
        self.cursor = self.conn.cursor()
        self.ib = IB()
        self.ib.connect(host="127.0.0.1", port=7496, clientId=1, readonly=True)
        for i in range(1, 5):
            self.ib.reqMarketDataType(i)

    def close(self):
        self.conn.commit()
        self.conn.close()
        self.ib.disconnect()

    def commit(self):
        self.conn.commit()

    def get_option_dividend_return(self, ticker, days_to_expiry) -> float:
        # TODO handle volatile dividends
        dividends = self.get_dividends(ticker).tz_convert("UTC")

        if len(dividends) == 0:
            return 0

        d = datetime.now()
        d = d.replace(year=d.year - 1)
        d = pytz.utc.localize(d)

        dividends_last_year = dividends[dividends.index.to_pydatetime() > d]

        if len(dividends_last_year) == 0:
            return 0

        dividend_days = 365 / len(dividends_last_year)
        days_since_last_dividend = (
            pytz.utc.localize(datetime.now())
            - dividends_last_year.index.to_pydatetime()[-1]
        ).days
        days_to_next_dividend = dividend_days - days_since_last_dividend

        if days_to_expiry < days_to_next_dividend:
            return 0

        dividend_count = (days_to_expiry - days_to_next_dividend) // dividend_days + 1
        recent_dividend = dividends_last_year.iloc[-1]

        return recent_dividend * dividend_count

    def get_option_annualized(self, option, stock_price):
        expiry_days = (utils.format_datetime(option.expiry) - datetime.now()).days
        dividend_return = self.get_option_dividend_return(option.symbol, expiry_days)

        call = option.optPrice
        strike = option.strike

        call_return = call + strike - stock_price
        total_return = call_return + dividend_return
        cost_base = stock_price - call

        annualized = pow(1 + total_return / cost_base, 365 / expiry_days) - 1

        return annualized

    def update_futures_data(self):
        print("Updating futures data")

        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS Futures (
                symbol TEXT PRIMARY KEY,
                price REAL
            )"""
        )

        positions = self.get_positions()
        for position in positions:
            if isinstance(position.contract, Future):
                symbol = position.contract.symbol
                price = self.get_contract_price(position.contract) 

        if price is None:
            price = 0

        sql = """INSERT OR REPLACE INTO Futures (symbol, price) VALUES (?, ?)"""
        self.cursor.execute(sql, [symbol, price])

    def update_rfr_data(self):
        print("Updating risk free rate data")

        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS RiskFreeRate (
                identifier TEXT PRIMARY KEY,
                rate REAL
            )"""
        )

        rate = yfinance.Ticker("^IRX").fast_info["lastPrice"] / 100

        sql = """INSERT OR REPLACE INTO RiskFreeRate (identifier, rate) VALUES (?, ?)"""
        self.cursor.execute(sql, ["US_13_Week", rate])

    def update_currency_data(self):
        print("Updating currency data")

        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS Currencies (
                pair TEXT PRIMARY KEY,
                price REAL
            )"""
        )

        contract = Contract()
        contract.symbol = "USD"
        contract.currency = "CAD"
        contract.secType = "CASH"
        contract.exchange = "IDEALPRO"

        # Request market data for USD/CAD
        price = self.ib.reqTickers(contract)[0].marketPrice()

        sql = """INSERT OR REPLACE INTO Currencies (pair, price) VALUES (?, ?)"""
        self.cursor.execute(sql, ["CAD/USD", price])

    def update_position_data(self):
        print("Updating position data")

        self.cursor.execute("""DROP TABLE IF EXISTS Positions;""")

        self.conn.commit()

        # Execute the Positions table creation SQL statement
        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS Positions (
                accountId TEXT,
                conId INT,
                data TEXT,
                PRIMARY KEY (accountId, conId)
            );"""
        )

        # Iterate through account positions and insert or replace them in the database
        account_list = self.ib.managedAccounts()
        for account in account_list:
            positions = self.ib.positions(account)
            for position in positions:
                sql = "INSERT OR REPLACE INTO positions (accountId, conId, data) VALUES (?, ?, ?)"
                values = [
                    position.account,
                    position.contract.conId,
                    jsonpickle.encode(position),
                ]
                self.cursor.execute(sql, values)

    def update_option_data(self):
        print("Updating option data")

        # Create the stocks table if it doesn't exist
        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS Options (
                            conId text PRIMARY KEY, 
                            data text
                            )"""
        )

        option_tickers = []
        stock_tickers = []
        positions = self.get_positions()
        for position in positions:
            if isinstance(position.contract, Option):
                self.ib.qualifyContracts(position.contract)
                ticker = self.ib.reqMktData(position.contract, "", False, False)
                option_tickers.append(ticker)

                # undPrice is None for some reason sometimes
                stock_contract = Stock(position.contract.symbol, "SMART", position.contract.currency)
                self.ib.qualifyContracts(stock_contract)
                stock_ticker = self.ib.reqMktData(position.contract, "", False, False)
                stock_tickers.append(stock_ticker)

        for _ in range(10):
            self.ib.sleep(0.2)

            for i, ticker in enumerate(option_tickers):
                if ticker.modelGreeks is not None:
                    option_data = OptionData(
                        ticker.contract.conId,
                        ticker.contract.symbol,
                        ticker.contract.lastTradeDateOrContractMonth,
                        ticker.contract.strike,
                        ticker.contract.right,
                        ticker.contract.exchange,
                        ticker.modelGreeks.optPrice,
                        stock_tickers[i].last,
                        ticker.modelGreeks.impliedVol,
                        ticker.modelGreeks.delta,
                        ticker.modelGreeks.gamma,
                        ticker.modelGreeks.vega,
                        ticker.modelGreeks.theta,
                    )

                    sql = """INSERT OR REPLACE INTO Options (conId, data) 
                                VALUES (?, ?)"""
                    values = [ticker.contract.conId, jsonpickle.encode(option_data)]
                    self.cursor.execute(sql, values)

    def update_stock_data(self):
        print("Updating stock data")

        # Create the stocks table if it doesn't exist
        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS Stocks (
                            symbol text PRIMARY KEY, 
                            data text
                            )"""
        )

        positions = self.get_positions()

        added_symbols = set()
        for position in positions:
            symbol = position.contract.symbol

            if symbol not in added_symbols and not isinstance(
                position.contract, Future
            ):
                added_symbols.add(symbol)

                self.ib.qualifyContracts(position.contract)

                ticker = yfinance.Ticker(yf_symbol(position.contract))

                stock_data = StockData(
                    info=ticker.info,
                    financials=ticker.financials,
                    balanceSheet=ticker.balancesheet,
                    cashFlow=ticker.cashflow,
                    dividends=ticker.dividends,
                    fast_info=ticker.fast_info,
                    option_chain=self.get_option_chain(position.contract),
                )

                sql = """INSERT OR REPLACE INTO Stocks (symbol, data) 
                            VALUES (?, ?)"""
                values = [symbol, jsonpickle.encode(stock_data)]
                self.cursor.execute(sql, values)

    def update_strategy_data(self):
        print("Updating strategy data")

        # TODO in future just do most recent date for get
        self.cursor.execute("DROP TABLE IF EXISTS Strategies;")
        self.conn.commit()

        # Create the stocks table if it doesn't exist
        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS Strategies (
                            row INT,
                            symbol TEXT, 
                            strategy TEXT,
                            PRIMARY KEY (row, symbol)
                            )"""
        )

        strategy_builder = StrategyBuilder(self.get_positions())

        db_items = strategy_builder.strategies_to_db()
        db_items.append(
            [
                0,
                "Cash",
                jsonpickle.encode(CashStrategyObject(self.get_cash_balance())),
            ]
        )

        sql = """INSERT OR REPLACE INTO Strategies (row, symbol, strategy) 
                    VALUES (?, ?, ?)"""

        for db_item in db_items:
            self.cursor.execute(sql, db_item)

    def get_dividends(self, ticker):
        # Execute the SELECT statement to retrieve dividend information for the given ticker
        stock_data = self.get_stock(ticker)
        return stock_data.dividends

    def get_options(self):
        rows = self.cursor.execute("SELECT * FROM Options").fetchall()
        return [jsonpickle.decode(row[1]) for row in rows if row[1] is not None]

    def get_option(self, conId):
        rows = self.cursor.execute(
            f"SELECT * FROM Options WHERE conId = ?", (conId,)
        ).fetchone()
        return jsonpickle.decode(rows[1])

    def get_positions(self):
        rows = self.cursor.execute("SELECT * FROM Positions").fetchall()
        return [jsonpickle.decode(row[2]) for row in rows if row[2] is not None]

    def get_position(self, accountId, conId):
        rows = self.cursor.execute(
            f"SELECT * FROM Strategies WHERE account = ? AND conId = ?",
            (accountId, conId),
        ).fetchone()
        return jsonpickle.decode(rows[2])

    def get_strategies(self):
        rows = self.cursor.execute("SELECT * FROM Strategies").fetchall()
        return [jsonpickle.decode(row[2]) for row in rows if row[2] is not None]

    def get_strategy(self, symbol):
        rows = self.cursor.execute(
            f"SELECT * FROM Strategies WHERE symbol = ?", (symbol,)
        ).fetchone()
        return jsonpickle.decode(rows[1])

    def get_stocks(self):
        rows = self.cursor.execute(f"SELECT * FROM Stocks").fetchall()
        return jsonpickle.decode(rows[1])

    def get_stock(self, symbol):
        rows = self.cursor.execute(
            f"SELECT * FROM Stocks WHERE symbol = ?", (symbol,)
        ).fetchone()
        return jsonpickle.decode(rows[1])

    def get_stock_price(self, ticker):
        contract = Stock(symbol=ticker, exchange="SMART", currency="USD")
        ticker = self.ib.reqTickers(contract)[0]
        return ticker.marketPrice()

    async def get_stock_price_async(self, ticker):
        contract = Stock(symbol=ticker, exchange="SMART", currency="USD")
        await self.ib.qualifyContracts(contract)
        ticker = await self.ib.reqTickersAsync(contract)
        return ticker[0].marketPrice()

    def get_contract_price(self, contract):
        self.ib.qualifyContracts(contract)
        ticker = self.ib.reqTickers(contract)[0]
        return ticker.marketPrice()

    def get_stock_details(self):
        # Define the stock contract
        stock_contract = Stock(
            "IMMR", "SMART", "USD"
        )  # Replace AAPL with your desired stock symbol

        # Request contract details
        # details = self.ib.reqContractDetails(stock_contract)

    def get_currency(self):
        rows = self.cursor.execute(f"SELECT * FROM Currencies").fetchone()
        return rows[1]

    def get_cash_balance(self):
        return sum(
            [
                float(x.value)
                for x in self.ib.accountValues()
                if x.tag == "CashBalance" and x.currency == "BASE"
            ]
        )

    def get_rfr(self):
        rows = self.cursor.execute(f"SELECT * FROM RiskFreeRate").fetchone()
        return rows[1]

    def get_futures_price(self):
        rows = self.cursor.execute(f"SELECT * FROM Futures").fetchone()
        return rows[1]

    def get_option_chain(self, stock_contract):
        self.ib.qualifyContracts(stock_contract)
        option_chains = self.ib.reqSecDefOptParams(
            stock_contract.symbol, "", stock_contract.secType, stock_contract.conId
        )
        return option_chains[0] if option_chains != [] else []


def yf_symbol(contract) -> str:
    symbol = contract.symbol
    exchange = contract.exchange

    s = symbol.replace(".", "-")
    if exchange == "TSE" or exchange == "CDE":
        s += ".TO"
    elif exchange == "VENTURE":
        s += ".V"
    elif exchange == "LSE":
        s += ".L"
    elif symbol == "MCD" or symbol == "M6B":
        s += "=F"
    return s


def yf_symbol_to_ibkr(symbol) -> str:
    return symbol.split(".")[0]
