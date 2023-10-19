from datetime import datetime
import os
import csv
import jsonpickle
import pandas as pd
import yfinance as yf
from src.asset import Asset
from screener import Screener

class DataProcessor:
    def __init__(self):
        self.tickers = None
        self.data = {}
        self.initialize()
    
    def initialize(self):
        self.organize_tickers()
        self.tickers = self.get_tickers("data/tickers/tickers.csv")

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

    def get_tickers(self, file_path):
        file = open(file_path)
        csvreader = csv.reader(file)

        return [row[0] for row in csvreader]

    def write_data(self, file_path):
        callable_list = ["info", "financials", "balancesheet", "cashflow", "dividends", "options", "option_chain"]
        total_time, count, length = 0, 0, len(self.tickers)
        for ticker_str in self.tickers:
            t1 = datetime.now()

            print(f"Fetching data for ticker: {ticker_str}")

            self.data[ticker_str] = {}
            for method in callable_list:
                self.data[ticker_str][method] = None
                try:
                    ticker = yf.Ticker(ticker_str)
                    data = getattr(ticker, method)

                    # Serialization/deserialization doesn't work for calls/puts without converting to/from dict
                    # TODO make option_chain call by target expiry
                    if method == "option_chain":
                        option_dates = self.data[ticker_str]["options"]
                        expiry_index = self.get_expiry_from_target_days(option_dates, 180)
                        expiry = option_dates[expiry_index]
                        data = ticker.option_chain(expiry) # date = expiry
                        option_chain = {}
                        option_chain["calls"] = data.calls.to_dict()
                        option_chain["puts"] = data.puts.to_dict()
                        data = option_chain
                        self.data[ticker_str]["option_chain_date"] = expiry

                    self.data[ticker_str][method] = data
                except:
                    print(f"Error calling {method}")

            t2 = datetime.now()
            total_time += (t2-t1).microseconds
            count += 1
            print(f"Took {(t2-t1).microseconds} microseconds to fetch {ticker_str} || Average: {total_time/count} || Total: {total_time} || Count: {count} || Estimated time remaining (m) {(length - count) * total_time/count / 1000000 / 60}")

        encoded = jsonpickle.encode(self.data)
        file = open(file_path, 'w', encoding="utf-8")
        file.write(encoded)
    
    def read_data(self, file_path):
        file = open(file_path, 'r', encoding="utf-8")
        file_json = file.read()
        decoded = jsonpickle.decode(file_json)

        for key, val in decoded.items():
            try:
                decoded[key]["option_chain"]["calls"] = pd.DataFrame.from_dict(decoded[key]["option_chain"]["calls"])
                decoded[key]["option_chain"]["puts"] = pd.DataFrame.from_dict(decoded[key]["option_chain"]["puts"])
            except:
                continue

        return decoded
    
    def organize_tickers(self):
        tickers = set()
        directory = "data/raw"
        for file_name in os.listdir(directory):
            file_path = os.path.join(directory, file_name)

            with open(file_path) as file:
                csvreader = csv.reader(file)
                next(csvreader)
                
                for row in csvreader:
                    tickers.add(row[0])

        tickers_input = []
        for ticker in tickers:
            tickers_input.append([ticker])
        
        with open("data/tickers/tickers.csv", "w") as file:
            csvwriter = csv.writer(file)
            csvwriter.writerows(tickers_input)

    def options_annualized(self, file_path):
        screener = Screener(None)
        options = screener.read_option(file_path)

        for option in options:
            print(option)
            a = Asset(option.ticker)
            annualized = a.get_option_annualized(option)
            print(f"annualized: {annualized}")
            ticker = yf.Ticker(option.ticker)
            beta = float(ticker.info['beta'])
            risk_free_rate = a.get_rate()
            market_rate = 0.1
            alpha = annualized - risk_free_rate - beta * (market_rate - risk_free_rate)
            print(f"beta: {beta}")
            print(f"alpha: {alpha}")
            print(f"sector: {ticker.info['sector']}")
            print(f"industry: {ticker.info['industry']}\n")

# dp = DataProcessor()
# dp.options_annualized("data/intrinsic_value/20231017.csv")
# dp.write_data('data/core/new_stock_data.pkl')
# data = dp.read_data('data/core/new_stock_data.pkl')

# print(data)




