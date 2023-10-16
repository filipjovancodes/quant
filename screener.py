import csv
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
    
    def screen_value(self):
        tickers = self.get_tickers()

        qualified = []

        for ticker in tickers[::-1]:
            # print(f"Checking {ticker}")

            a = Asset(ticker)

            try: 
                share_issued = a.get_share_issued()
                price = a.get_price()
                mcap = price * share_issued

                nd = a.get_net_debt()
                cf = a.get_cash_flow_avg()

                pe = a.get_pe()

                print(ticker, nd, mcap, cf, pe, a.get_intrinsic_value())

                if nd / mcap > 0.7 and cf / mcap > 0.1 and pe < 10:
                    print(f"Qualified {ticker}")
                    qualified.append(ticker)
            except: 
                continue

screener = Screener("data/russell-3000.csv")

tickers = screener.screen_value()

print(tickers)