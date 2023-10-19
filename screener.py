import csv

import yfinance as yf
import src.option
from datetime import datetime
from yahoo_fin import stock_info as si
from src.asset import Asset
from src.asset_position import AssetPosition

class Screener:
    def __init__(self, data_path):
        self.data_path = data_path

    def get_tickers(self):
        file = open(self.data_path)
        csvreader = csv.reader(file)
        next(csvreader)

        return [row[0] for row in csvreader]
    
    # TODO move to format file
    def format_date(self, year: int, month: int, day: int) -> str:
        output = str(year)
        m = str(month)
        if len(m) == 1:
            m = "0" + m
        output += m
        d = str(day)
        if len(d) == 1:
            d = "0" + d
        output += d

        return output
    
    def write_file(self, qualified, name):
        today = datetime.now()
        today_formatted = self.format_date(today.year, today.month, today.day)
        header = ["ticker", "price", "share_issued", "mcap", "nd", \
                    "cf", "pe", "ticker", "right", "stock_price", "strike", \
                    "expiry", "rate", "iv", "option_price", "delta", \
                    "gamma", "vega", "rho", "theta"]
        with open(f"data/{name}/{today_formatted}.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(qualified)

    def write_stock_data(self, stock_data):
        header = ["Ticker","Share Issued","Stock Price","Market Cap",\
                  "Net Debt", "Cash Flow (5y avg)","Price to Earnings",\
                  "Intrinsic Value","Dividend Yield","Financials Exchange Rate"]
        
        header = ["Ticker", "Revenue"]
        with open(f"data/core/stock_data.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(stock_data)

    def write_option_data(self, option_data):
        header = ["Ticker","Right","Stock Price","Strike","Expiry Date",\
                  "Interest Rate","Implied Volatility","Option Price",\
                    "Delta","Gamma","Vega","Rho","Theta"]
        with open(f"data/core/option_data.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(option_data)

    def flush_data(self, qualified, stock_data, option_data, name):
        self.write_stock_data(stock_data)
        self.write_option_data(option_data)
        self.write_file(qualified, name)

    # TODO from ticker csv put this into a csv with all data used for screener
    def get_core(self, a: Asset):
        share_issued = a.get_share_issued()
        price = a.get_price()
        mcap = price * share_issued

        nd = a.get_net_debt()
        cf = a.get_cash_flow_avg()
        pe = a.get_pe()
        intrinsic = a.get_intrinsic_value()

        return share_issued, price, mcap, nd, cf, pe, intrinsic

    # def screen_liquidation_value(self):
    #     tickers = self.get_tickers()
    #     qualified, stock_data, option_data = [], [], []
    #     for ticker in tickers:
    #         try: 
    #             a = Asset(ticker)
    #             share_issued, price, mcap, nd, cf, pe, intrinsic = self.get_core(a)

    #             stock_data.append([ticker, price, share_issued, mcap, nd, cf, pe, intrinsic])

    #             if nd / mcap > 0.7 and cf / mcap > 0.1 and pe < 10:
    #                 print(f"Qualified {ticker}")

    #                 option = a.get_option(nd, price)

    #                 data = [ticker, price, share_issued, mcap, nd, cf, pe, intrinsic] + option.to_list()
    #                 qualified.append(data)
    #                 print(data)
    #                 option_data.append(option.to_list())
    #         except: 
    #             continue

    #     self.flush_data(qualified, stock_data, option_data, "liquidation_value")
            
    #     return qualified 
    
    def screen_intrinsic_value(self):
        tickers = self.get_tickers()
        qualified, stock_data, option_data = [], [], []
        for ticker in tickers:
            try: 
                a = Asset(ticker)
                share_issued, price, mcap, nd, cf, pe, intrinsic = self.get_core(a)

                stock_data.append([ticker, price, share_issued, mcap, nd, cf, pe, intrinsic])
                
                if nd / mcap > 0.3 and cf / mcap > 0.1 and pe < 10 and intrinsic / price > 1:
                    print(f"Qualified {ticker}")

                    option = a.get_option(nd, price)

                    data = [ticker, price, share_issued, mcap, nd, cf, pe, intrinsic] + option.to_list()
                    qualified.append(data)
                    print(data)
                    option_data.append(option.to_list())
            except: 
                continue

        self.flush_data(qualified, stock_data, option_data, "intrinsic_value")
            
        return qualified 

    
    def read_option(self, file_path) -> list[src.option.Option]:
        header = ["ticker", "price", "share_issued", "mcap", "nd", "cf", "pe", "intrinsic", "ticker", "right", "stock_price", "strike", "expiry", "rate", "iv", "option_price", "delta", "gamma", "vega", "rho", "theta"]

        options = []
        with open(file_path) as file:
            csvreader = csv.reader(file, delimiter = ",")
            next(csvreader)

            for row in csvreader:
                print(row)
                if row[8] != "":
                    options.append(src.option.Option(
                            row[8],
                            row[9],
                            float(row[10]),
                            float(row[11]),
                            row[12],
                            float(row[13]),
                            float(row[14]),
                            float(row[15]),
                            float(row[16]),
                            float(row[17]),
                            float(row[18]),
                            float(row[19]),
                            float(row[20])
                        )
                    )

        return options
            
    
# screener = Screener("data/tickers/tickers.csv")
# screener.screen_liquidation_value()
# screener.screen_intrinsic_value()


    