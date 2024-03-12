import threading
import sqlite3
import csv
import yfinance
import jsonpickle

from local_objects import StockData

class YourClassName:
    def __init__(self):
        # Remove SQLite connection and cursor initialization from __init__
        pass

    def update_tickers_table(self, tickers):
        conn = sqlite3.connect("main.db")
        cursor = conn.cursor()

        cursor.execute(
            """CREATE TABLE IF NOT EXISTS Tickers (
                ticker TEXT PRIMARY KEY
            )"""
        )

        sql = """INSERT OR REPLACE INTO Tickers (ticker) 
                        VALUES (?)"""
        for ticker in tickers: 
            cursor.execute(sql, [ticker])
            conn.commit()

        conn.close()

    def update_currencies_table(self):
        def yf_currency_symbol(numerator, denominator) -> str:
            if numerator == "USD":
                return denominator + "=X"
            
            return numerator + denominator + "=X"

        conn = sqlite3.connect("main.db")
        cursor = conn.cursor()

        cursor.execute(
            """CREATE TABLE IF NOT EXISTS Forex (
                currency TEXT PRIMARY KEY,
                price REAL
            )"""
        )

        sql = """INSERT OR REPLACE INTO Forex (currency, price) 
                        VALUES (?, ?)"""
        for currency in self.get_currency_symbols():
            try:
                print(f"Added {currency}")
                to_usd_symbol = yf_currency_symbol(currency, "USD")
                to_usd_ticker = yfinance.Ticker(to_usd_symbol)
                price = to_usd_ticker.fast_info["lastPrice"]

                cursor.execute(sql, [currency, price])
                conn.commit()
            except Exception as e:
                print(e)

        conn.close()

    def create_table(self):
        # Create SQLite connection and cursor within this method
        conn = sqlite3.connect("main.db")
        cursor = conn.cursor()

        cursor.execute(
            """CREATE TABLE IF NOT EXISTS ScreenerData (
                symbol TEXT PRIMARY KEY,
                data REAL
            )"""
        )

        # Commit changes and close connection
        conn.commit()
        conn.close()

    def get_ticker_symbols(self):
        with open("data/tickers/tickers.csv", 'r', encoding="utf-8") as file:
            csvreader = csv.reader(file) # TODO move away from csv
            return [row[0] for row in csvreader]
        
    def get_currency_symbols(self):
        with open("data/currency/currency.csv", 'r', encoding="utf-8") as file:
            csvreader = csv.reader(file) # TODO move away from csv
            return [row[0] for row in csvreader]
        
    def get_data1(self, symbol):
        try:
            # Create SQLite connection and cursor within this method
            conn = sqlite3.connect("main.db")
            cursor = conn.cursor()

            ticker = yfinance.Ticker(symbol)
            stock_data = StockData(
                info=ticker.info,
                financials=ticker.financials,
                balanceSheet=ticker.balancesheet,
                cashFlow=ticker.cashflow,
                dividends=ticker.dividends,
                fast_info=ticker.fast_info,
                option_chain=None,
            )

            sql = """INSERT OR REPLACE INTO ScreenerData (symbol, data) 
                        VALUES (?, ?)"""
            values = [symbol, jsonpickle.encode(stock_data)]
            cursor.execute(sql, values)
            conn.commit()

            # Close connection
            conn.close()

        except Exception as e:
            print(e)

    def get_ticker_data(self, tickers):
        for ticker in tickers:
            self.get_data1(ticker)

    def run_threads(self):
        max_thread_num = 10
        ticker_list_split = [self.get_ticker_symbols()[i::max_thread_num] for i in range(max_thread_num)]
        
        threads = []
        for tickers in ticker_list_split:
            thread = threading.Thread(target=self.get_ticker_data, args=(tickers,))
            thread.start()
            threads.append(thread)

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

    def get_tickers(self):
        conn = sqlite3.connect("main.db")
        cursor = conn.cursor()
        rows = cursor.execute("SELECT * FROM Tickers").fetchall()
        conn.close()
        return [row[0] for row in rows]

    def get_screener_data(self):
        conn = sqlite3.connect("main.db")
        cursor = conn.cursor()
        rows = cursor.execute("SELECT * FROM ScreenerData").fetchall()
        conn.close()
        return [jsonpickle.decode(row[1]) for row in rows if row[1] is not None]
    
    def get_exchange_rate(self, currency):
        conn = sqlite3.connect("main.db")
        cursor = conn.cursor()
        rows = cursor.execute("SELECT * FROM Forex WHERE currency = ?", (currency,)).fetchone()
        conn.close()
        return rows[1]
    
    def get_forex_rate(self, numerator, denominator):
        return self.get_exchange_rate(numerator) / self.get_exchange_rate(denominator)

    def get_financials_exchange_rate(self, stock_data):
        trade_currency = stock_data.info["currency"]
        financials_currency = stock_data.info["financialCurrency"]
        return self.get_forex_rate(financials_currency, trade_currency)

    def get_share_issued(self, stock_data):
        return stock_data.balanceSheet.loc["Share Issued"].iloc[0]

    def get_stock_price(self, stock_data):
        info = stock_data.info
        if info["quoteType"] == "ETF":
            return (info["ask"] - info["bid"])/2 + info["bid"]
        return info["currentPrice"]
    
    def get_net_debt(self, stock_data):
        # TODO
        return stock_data.balanceSheet.loc["Total Equity Gross Minority Interest"].iloc[0]  * self.get_financials_exchange_rate(stock_data)
    
    def get_shareholders_equity(self, stock_data):
        return stock_data.balanceSheet.loc["Total Equity Gross Minority Interest"].iloc[0]  * self.get_financials_exchange_rate(stock_data)

    def get_cashflow_avg(self, stock_data):
        return stock_data.cashFlow.loc["Free Cash Flow"].mean() * self.get_financials_exchange_rate(stock_data)

    def get_cashflow_last_year(self, stock_data):
        return stock_data.cashFlow.loc["Free Cash Flow"].iloc[0]

    def get_eps(self, stock_data):
        return stock_data.financials.loc["Basic EPS"].iloc[0]
    
    def get_pe(self, stock_data):
        return stock_data.info["currentPrice"] / self.get_eps(stock_data)
    
    def industry(self, stock_data):
        return stock_data.info["industry"] if "industry" in stock_data.info else ""

    def get_intrinsic_value(self, cashflow, net_debt, stock_price, share_issued):
        valuation = cashflow * 10
        lv = net_debt + valuation

        mcap = stock_price * share_issued
        share_iv = lv / mcap * stock_price

        return share_iv
    
    def get_liquidation_value(self, net_debt, stock_price, share_issued):
        mcap = stock_price * share_issued
        return net_debt / mcap

    def screen_stocks(self):
        stock_data_list = self.get_screener_data()

        qualified = []
        for stock_data in stock_data_list:
            try:
                share_issued = self.get_share_issued(stock_data)
                stock_price = self.get_stock_price(stock_data)
                mcap = share_issued * stock_price
                pe = self.get_pe(stock_data)
                eps = self.get_eps(stock_data)
                shareholders_equity = self.get_shareholders_equity(stock_data)
                cashflow = self.get_cashflow_avg(stock_data)
                intrinsic = self.get_intrinsic_value(cashflow, shareholders_equity, stock_price, share_issued)
                liquidation = self.get_liquidation_value(shareholders_equity, stock_price, share_issued)
                industry = self.industry(stock_data)

                score = 0
                if mcap > 3000000000 and "Bank" not in industry and "Insurance" not in industry:
                    score += min(10, (intrinsic / stock_price)) * 0.5 # dcf value
                    score += min(10, (liquidation / stock_price)) * 0.5 # liquidation value

                    qualified.append([score, stock_data])

            except Exception as error:
                print(error)

        qualified = sorted(qualified, key=lambda x: x[0], reverse=True)

        for (score, stock_data) in qualified[:100]:
            # share_issued = self.get_share_issued(stock_data)
            # stock_price = self.get_stock_price(stock_data)
            # mcap = share_issued * stock_price
            # pe = self.get_pe(stock_data)
            # eps = self.get_eps(stock_data)
            # shareholders_equity = self.get_shareholders_equity(stock_data)
            # cashflow = self.get_cashflow_avg(stock_data)
            # liquidation = self.get_liquidation_value(shareholders_equity, stock_price, share_issued)
            # intrinsic = self.get_intrinsic_value(cashflow, shareholders_equity, stock_price, share_issued)
            # print(mcap, intrinsic, liquidation)

            print(score, stock_data.info["symbol"], stock_data.info["industry"] if "industry" in stock_data.info else "")

if __name__ == "__main__":
    your_instance = YourClassName()
    # your_instance.create_table()
    # your_instance.run_threads()

    # your_instance.update_currencies_table()
    # print(your_instance.get_exchange_rate("CAD"))

    print(your_instance.screen_stocks())

