import csv
import traceback

import pandas
from archive.data_dao import DataDAO
from archive.data_processor import DataProcessor

import src.option
from datetime import datetime
import utils.utils as utils

class Screener:
    def __init__(self):
        self.data_dao = DataDAO()
    
    def write_file(self, qualified, name):
        today_formatted = utils.format_date(datetime.now())
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
        self.data_dao.data_processor.write_data(option_data, "data/core/option_data.pkl")

    def flush_data(self, qualified, stock_data, option_data, name):
        self.write_stock_data(stock_data)
        self.write_option_data(option_data)
        self.write_file(qualified, name)

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

    def get_intrinsic_value(self, cashflow, net_debt, stock_price, share_issued):
        valuation = cashflow * 10
        lv = net_debt + valuation

        mcap = stock_price * share_issued
        share_iv = lv / mcap * stock_price

        return share_iv
    
    def screen_intrinsic_value(self):
        qualified, stock_data, option_data = [], [], []
        for ticker in self.data_dao.tickers:
            try:
                share_issued = self.data_dao.get_share_issued(ticker)
                stock_price = self.data_dao.get_stock_price(ticker)
                mcap = share_issued * stock_price
                net_debt = self.data_dao.get_net_debt(ticker)
                cashflow = self.data_dao.get_cashflow_avg(ticker)
                pe = self.data_dao.get_pe(ticker)
                eps = self.data_dao.get_eps(ticker)
                intrinsic = self.get_intrinsic_value(cashflow, net_debt, stock_price, share_issued)

                stock_data.append([ticker, stock_price, share_issued, mcap, net_debt, cashflow, pe, intrinsic])
                
                if net_debt / mcap > 0.3 and cashflow / mcap > 0.1 and pe < 15 and intrinsic / stock_price > 1 and eps > 0:
                    print(f"Qualified {ticker}")
                    qualified.append(stock_data[-1])
                    # option = self.data_dao.get_option(ticker, net_debt, stock_price)
                    # print(option)
                    # option_data.append(option)
                    # qualified.append(stock_data[-1] + option_data[-1].to_list())
            except Exception as error:
            #     if not type(error) == KeyError:
            #         print(traceback.format_exc())
                print(error)

    def screen_intrinsic_value_last_year(self):
        qualified, stock_data, option_data = [], [], []
        for ticker in self.data_dao.tickers:
            try:
                er = self.data_dao.get_financials_exchange_rate(ticker)
                share_issued = self.data_dao.get_share_issued(ticker)
                stock_price = self.data_dao.get_stock_price(ticker)
                mcap = share_issued * stock_price
                net_debt = self.data_dao.get_net_debt(ticker) * er
                cashflow = self.data_dao.get_cashflow_last_year(ticker) * er
                pe = self.data_dao.get_pe(ticker)
                eps = self.data_dao.get_eps(ticker)
                intrinsic = self.get_intrinsic_value(cashflow, net_debt, stock_price, share_issued)

                stock_data.append([ticker, stock_price, share_issued, mcap, net_debt, cashflow, pe, eps, intrinsic])
                
                if net_debt / mcap > 0.3 and cashflow / mcap > 0.1 and pe < 15 and intrinsic / stock_price > 1 and eps > 0:
                    print(f"Qualified {ticker}")
                    qualified.append(stock_data[-1])
                    # option = self.data_dao.get_option(ticker, net_debt, stock_price)
                    # print(option)
                    # option_data.append(option)
                    # qualified.append(stock_data[-1] + option_data[-1].to_list())
            except Exception as error:
            #     if not type(error) == KeyError:
            #         print(traceback.format_exc())
                print(error)

        self.flush_data(qualified, stock_data, option_data, "intrinsic_value_last_year")
            
        return qualified 
    
    def screen_intrinsic_value_last_year_loose(self):
        qualified, stock_data, option_data = [], [], []
        for ticker in self.data_dao.tickers:
            try:
                er = self.data_dao.get_financials_exchange_rate(ticker)
                share_issued = self.data_dao.get_share_issued(ticker)
                stock_price = self.data_dao.get_stock_price(ticker)
                mcap = share_issued * stock_price
                net_debt = self.data_dao.get_net_debt(ticker) * er
                cashflow = self.data_dao.get_cashflow_last_year(ticker) * er
                pe = self.data_dao.get_pe(ticker)
                eps = self.data_dao.get_eps(ticker)
                intrinsic = self.get_intrinsic_value(cashflow, net_debt, stock_price, share_issued)

                stock_data.append([ticker, stock_price, share_issued, mcap, net_debt, cashflow, pe, eps, intrinsic])

                if net_debt / mcap > 0.3 and cashflow / mcap > 0.08 and pe < 20 and intrinsic / stock_price > 0.75 and eps > 0:
                    print(f"Qualified {ticker}")
                    qualified.append(stock_data[-1])
                    # option = self.data_dao.get_option(ticker, net_debt, stock_price)
                    # print(option)
                    # option_data.append(option)
                    # qualified.append(stock_data[-1] + option_data[-1].to_list())
            except Exception as error:
            #     if not type(error) == KeyError:
            #         print(traceback.format_exc())
                print(error)

        self.flush_data(qualified, stock_data, option_data, "intrinsic_value_last_year")
            
        return qualified 
    
    # TODO move to data formats file (which will become output for dashboard)
    # ex options_annualized
    def option_strategy_data(self):
        options: list[src.option.Option] = self.data_dao.data_processor.read_data("data/core/option_data.pkl")

        for option in options:
            try:
                ticker = option.ticker
                print(f"ticker: {ticker}")
                annualized = self.data_dao.get_option_annualized(option)
                print(f"annualized: {annualized}")
                beta = self.data_dao.get_beta(ticker)
                risk_free_rate = self.data_dao.interest_rate
                market_rate = 0.1
                alpha = annualized - risk_free_rate - beta * (market_rate - risk_free_rate)
                print(f"beta: {beta}")
                print(f"alpha: {alpha}")
                # print(f"sector: {self.data_dao.stock_data[ticker]['info']['sector']}")
                # print(f"industry: {self.data_dao.stock_data[ticker]['info']['industry']}\n")
            except:
                print(traceback.format_exc())
            
    
screener = Screener()
# screener.screen_liquidation_value()
# screener.screen_intrinsic_value()
# screener.option_strategy_data()
# screener.screen_intrinsic_value_last_year()
screener.screen_intrinsic_value_last_year_loose()


    