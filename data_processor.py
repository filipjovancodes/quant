from datetime import datetime
import os
import csv
import traceback
import jsonpickle
import pandas as pd
import yfinance as yf
import utils.yf_utils as yf_utils
from src.option import Option


class DataProcessor:
    def __init__(self):
        self.tickers = None
        self.stock_data = {}
        self.currency_data = {}
        self.initialize()
    
    def initialize(self):
        self.organize_tickers("data/tickers/tickers.csv")
        self.tickers = self.get_symbols("data/tickers/tickers.csv")
        self.currencies = self.get_symbols("data/currency/currency.csv")

    def get_expiry_from_target_days(self, valid_option_dates, target_days_to_expiry):
        if len(valid_option_dates) == 0:
            return ""

        # index, smallest time difference
        result = [0, target_days_to_expiry]
        today = datetime.now()
        for i, date in enumerate(valid_option_dates):
            days_diff = abs((datetime.strptime(date, "%Y-%m-%d") - today).days - target_days_to_expiry)
            if days_diff < result[1]:
                result = [i, days_diff]

        return result[0]
    
    def get_symbols(self, file_path):
        with open(file_path, 'r', encoding="utf-8") as file:
            csvreader = csv.reader(file)
            return [row[0] for row in csvreader]
    
    def write_data(self, data, file_path):
        encoded = jsonpickle.encode(data)
        with open(file_path, 'w', encoding="utf-8") as file:
            file.write(encoded)
    
    def write_currency_data(self, file_path):
        for currency in self.currencies:
            try:
                print(f"Added {currency}")
                to_usd_symbol = yf_utils.yf_currency_symbol(currency, "USD")
                to_usd_ticker = yf.Ticker(to_usd_symbol)
                self.currency_data[currency] = to_usd_ticker.fast_info["lastPrice"]
            except:
                print(traceback.format_exc())

        self.write_data(self.currency_data, file_path)

    def update_stock_data(self, ticker_str):
        self.stock_data[ticker_str] = {}
        for method in ["info", "financials", "balancesheet", "cashflow", "dividends", "options", "option_chain"]:
            self.stock_data[ticker_str][method] = None
            try:
                ticker = yf.Ticker(ticker_str)
                data = getattr(ticker, method)

                # Serialization/deserialization doesn't work for calls/puts without converting to/from dict
                if method == "option_chain":
                    option_dates = self.stock_data[ticker_str]["options"]
                    expiry_index = self.get_expiry_from_target_days(option_dates, 180)
                    expiry = option_dates[expiry_index]
                    data = ticker.option_chain(expiry) # date = expiry
                    option_chain = {}
                    option_chain["calls"] = data.calls.to_dict()
                    option_chain["puts"] = data.puts.to_dict()
                    data = option_chain
                    self.stock_data[ticker_str]["option_chain_date"] = expiry

                self.stock_data[ticker_str][method] = data
            except:
                print(f"Error calling {method}")

    def write_stock_data(self, file_path, tickers_input = None):
        tickers_to_use = self.tickers
        if tickers_input is not None:
            tickers_to_use = tickers_input

        total_time, count, length = 0, 0, len(tickers_to_use)
        for ticker_str in tickers_to_use:
            t1 = datetime.now()
            print(f"Fetching data for ticker: {ticker_str}")

            self.update_stock_data(ticker_str)

            t2 = datetime.now()
            total_time += (t2-t1).microseconds
            count += 1
            print(f"Took {(t2-t1).microseconds} microseconds to fetch {ticker_str} || Average: {total_time/count} || Total: {total_time} || Count: {count} || Estimated time remaining (m) {(length - count) * total_time/count / 1000000 / 60}")

            individual_stock_file_path = f"data/stock_data/{ticker_str}.pkl"
            self.write_data(self.stock_data[ticker_str], individual_stock_file_path)

        self.write_data(self.stock_data, file_path)
    
    def read_stock_data(self, file_path):
        with open(file_path, 'r', encoding="utf-8") as file:
            file_json = file.read()
        decoded = jsonpickle.decode(file_json)

        for key, val in decoded.items():
            try:
                decoded[key]["option_chain"]["calls"] = pd.DataFrame.from_dict(decoded[key]["option_chain"]["calls"])
                decoded[key]["option_chain"]["puts"] = pd.DataFrame.from_dict(decoded[key]["option_chain"]["puts"])
            except:
                print("Error decoding options chain")
                continue

        return decoded
    
    def read_individual_stock_data(self, file_path):
        with open(file_path, 'r', encoding="utf-8") as file:
            file_json = file.read()
        decoded = jsonpickle.decode(file_json)

        for key, val in decoded.items():
            try:
                decoded["option_chain"]["calls"] = pd.DataFrame.from_dict(decoded["option_chain"]["calls"])
                decoded["option_chain"]["puts"] = pd.DataFrame.from_dict(decoded["option_chain"]["puts"])
            except:
                print("Error decoding options chain")
                continue

        return decoded
    
    def read_data(self, file_path):
        with open(file_path, 'r', encoding="utf-8") as file:
            file_json = file.read()
        return jsonpickle.decode(file_json)
    
    def update_stock_data_file(self, file_path, tickers_input = None):
        tickers_to_use = self.tickers
        if tickers_input is not None:
            tickers_to_use = tickers_input

        self.stock_data = self.read_data(file_path)

        total_time, count, length = 0, 0, len(tickers_to_use)

        for ticker_str in tickers_to_use:
            t1 = datetime.now()
            print(f"Fetching data for ticker: {ticker_str}")

            self.update_stock_data(ticker_str)

            t2 = datetime.now()
            total_time += (t2-t1).microseconds
            count += 1
            print(f"Took {(t2-t1).microseconds} microseconds to fetch {ticker_str} || Average: {total_time/count} || Total: {total_time} || Count: {count} || Estimated time remaining (m) {(length - count) * total_time/count / 1000000 / 60}")

        self.write_data(self.stock_data, file_path)
    
    def organize_tickers(self, file_path):
        tickers = set()
        directory = "data/raw"
        for file_name in os.listdir(directory):
            data_file_path = os.path.join(directory, file_name)

            with open(data_file_path, 'r', encoding="utf-8") as file:
                csvreader = csv.reader(file)
                next(csvreader)
                
                for row in csvreader:
                    tickers.add(row[0])

        tickers_input = []
        for ticker in tickers:
            tickers_input.append([ticker])
        
        with open(file_path, 'w', encoding="utf-8") as file:
            csvwriter = csv.writer(file)
            csvwriter.writerows(tickers_input)

dp = DataProcessor()
# dp.options_annualized("data/intrinsic_value/20231017.csv")
# dp.write_stock_data('data/core/new_stock_data.pkl')
# data = dp.read_data('data/core/new_stock_data.pkl')
# dp.write_currency_data("data/core/currency_data.pkl")
# print(dp.read_currency_data("data/core/currency_data.pkl"))

ticker_str = "FRT"
print(dp.read_individual_stock_data(f"data/stock_data/{ticker_str}.pkl"))

# tickers = ["ABNB", "SXP.TO", "MRG-UN.TO", "APR-UN.TO", "RET-A.V"]
# dp.write_stock_data('data/core/test.pkl', tickers)
# dp.update_stock_data_file("data/core/new_stock_data.pkl", tickers)

# dp = DataProcessor()
# data = dp.read_stock_data("data/core/new_stock_data.pkl")

# print(data["DHT"])
# print(data["RET-A.V"])

# print(data["UMC"])



