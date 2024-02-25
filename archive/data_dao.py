from dateutil.relativedelta import relativedelta
from datetime import datetime
import math
import pytz

import yfinance as yf
from archive.data_processor import DataProcessor
from src.option import Option
import src.black_scholes as black_scholes
import utils.utils as utils


class DataDAO:
    def __init__(self):
        self.data_processor = DataProcessor()
        self.initialize()

    def initialize(self):
        self.stock_data = self.data_processor.read_stock_data_from_directory("data/stock_data")
        self.tickers = [ticker for ticker, _ in self.stock_data.items()]
        self.currency_data = self.data_processor.read_data("data/core/currency_data.pkl")
        self.interest_rate = yf.Ticker("^IRX").fast_info["lastPrice"]/100 # TODO add to file?

    def get_exchange_rate(self, numerator, denominator):
        return self.currency_data[numerator] / self.currency_data[denominator]

    def get_financials_exchange_rate(self, ticker):
        trade_currency = self.stock_data[ticker]["info"]["currency"]
        financials_currency = self.stock_data[ticker]["info"]["financialCurrency"]
        return self.get_exchange_rate(financials_currency, trade_currency)

    def get_stock_price(self, ticker):
        info = self.stock_data[ticker]["info"]
        if info["quoteType"] == "ETF":
            return (info["ask"] - info["bid"])/2 + info["bid"]
        return info["currentPrice"]
    
    def get_share_issued(self, ticker):
        return self.stock_data[ticker]["balancesheet"].loc["Share Issued"].iloc[0]

    def get_net_debt(self, ticker):
        # TODO
        return self.stock_data[ticker]["balancesheet"].loc["Total Equity Gross Minority Interest"].iloc[0]  * self.get_financials_exchange_rate(ticker)
        # return self.get_current_assets(ticker) - self.get_total_debt(ticker) 

    def get_total_debt(self, ticker):
        bs = self.stock_data[ticker]["balancesheet"]
        try:
            td = bs.loc["Total Debt"].iloc[0]
        except KeyError:
            td = bs.loc["Total Liabilities Net Minority Interest"].iloc[0]
        return td * self.get_financials_exchange_rate(ticker)
    
    def get_current_assets(self, ticker):
        return self.stock_data[ticker]["balancesheet"].loc["Current Assets"].iloc[0]  * self.get_financials_exchange_rate(ticker)
    
    def get_cashflow_avg(self, ticker):
        return self.stock_data[ticker]["cashflow"].loc["Free Cash Flow"].mean() * self.get_financials_exchange_rate(ticker)

    def get_cashflow_last_year(self, ticker):
        return self.stock_data[ticker]["cashflow"].loc["Free Cash Flow"].iloc[0]
    
    def get_eps(self, ticker):
        return self.stock_data[ticker]["financials"].loc["Basic EPS"].iloc[0]
    
    def get_pe(self, ticker):
        return (self.stock_data[ticker]["info"]["currentPrice"] / self.get_eps(ticker))
    
    def get_beta(self, ticker):
        return self.stock_data[ticker]["info"]["beta"]
    
    def get_rate(self, ticker):
        pass

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
    
    # TODO refactor to be similar to get_expiry_from_target_days
    def get_strike(self, target_strike, strikes):
        target_strike = math.floor(target_strike)
        max_itr_strike = 100
        j = 0
        result_strike = None
        while j < max_itr_strike:
            strike_check = [target_strike - 0.25 * j, target_strike + 0.25 * j]
            for strike in strike_check:
                if strike in strikes:
                    result_strike = strike
                    j = max_itr_strike
                    break
            j += 1

        return result_strike
    
    def get_option_ibkr(self, option_ticker_data) -> Option:
        print(option_ticker_data)
        return Option(
            ticker = option_ticker_data.contract.symbol,
            right = option_ticker_data.contract.right,
            stock_price = option_ticker_data.modelGreeks.undPrice,
            strike = option_ticker_data.contract.strike,
            expiry = option_ticker_data.contract.lastTradeDateOrContractMonth,
            rate = None,
            iv = option_ticker_data.modelGreeks.impliedVol,
            option_price = option_ticker_data.modelGreeks.optPrice,
            delta = option_ticker_data.modelGreeks.delta,
            gamma = option_ticker_data.modelGreeks.gamma,
            vega = option_ticker_data.modelGreeks.vega,
            rho = None,
            theta = option_ticker_data.modelGreeks.theta
        )

    def get_option(self, ticker, net_debt, stock_price) -> Option:
        if self.stock_data[ticker]["option_chain"] is None:
            return Option()

        if net_debt > stock_price:
            net_debt = stock_price * 0.9

        target_strike = math.floor(net_debt)
        calls = self.stock_data[ticker]["option_chain"]["calls"]
        strikes = calls["strike"].values
        result_strike = self.get_strike(target_strike, strikes)
        option_row = calls.loc[calls["strike"] == result_strike].iloc[0]

        return self.get_option_from_iv(
            ticker = ticker,
            row = option_row,
            right = "C",
            strike = result_strike,
            contractDate = self.stock_data[ticker]["option_chain_date"]
        )
    
    def get_option_price(self, row):
        bid, ask = row["bid"], row["ask"]
        if bid != 0 and ask != 0:
            return bid + (ask - bid) / 2
        return row["lastPrice"]
    
    def get_option_from_iv(self, ticker: str, row, right: str, strike: float, contractDate: str) -> Option:
        option_price = self.get_option_price(row)
        days_to_expiry = (utils.format_datetime(contractDate) - datetime.now()).days
        stock_price = self.get_stock_price(ticker)

        iv = row["impliedVolatility"]
        use_new_option_price = False
        if iv < 0.05:
            iv = black_scholes.implied_volatility(option_price, stock_price, strike, days_to_expiry/365, self.interest_rate, right)
            use_new_option_price = True

        new_option_price, delta, gamma, vega, rho, theta = black_scholes.get_price_and_greeks(
            S = stock_price,
            K = strike,
            T = days_to_expiry/365,
            r = self.interest_rate,
            iv = iv,
            right = right
        )
        
        if use_new_option_price is True:
            option_price = new_option_price

        op = Option(
            ticker = ticker,
            right = right,
            stock_price = stock_price,
            strike = strike,
            expiry = contractDate,
            rate = self.interest_rate,
            iv = iv,
            option_price = option_price,
            delta = delta,
            gamma = gamma, 
            vega = vega,
            rho = rho, 
            theta = theta
        )

        return op
    
    def get_option_dividend_return(self, ticker, days_to_expiry) -> float:
        # get dividends over the last year
        # common: 4, 12 process as such else weird and flag and handle later
        dividends = self.stock_data[ticker]["dividends"].tz_convert("UTC")

        if len(dividends) == 0:
            return 0

        d = datetime.now()
        d = d.replace(year = d.year - 1)
        d = pytz.utc.localize(d)

        dividends_last_year = dividends[dividends.index.to_pydatetime() > d]

        if len(dividends_last_year) == 0:
            return 0

        dividend_days = 365/len(dividends_last_year)
        days_since_last_dividend = (datetime.now() - dividends_last_year.index.to_pydatetime()[-1]).days
        days_to_next_dividend = dividend_days - days_since_last_dividend

        if days_to_expiry < days_to_next_dividend:
            return 0
        
        dividend_count = (days_to_expiry - days_to_next_dividend) // dividend_days + 1
        recent_dividend = dividends_last_year.iloc[-1]["dividend"]

        return recent_dividend * dividend_count
    
    # TODO refactor option expected return
    def get_option_annualized(self, option: Option):

        expiry_days = (utils.format_datetime(option.expiry) - datetime.now()).days
        dividend_return = self.get_option_dividend_return(option.ticker, expiry_days)
        
        call = option.option_price
        stock = option.stock_price
        strike = option.strike
        
        call_return = call + strike - stock
        total_return = call_return + dividend_return
        cost_base = stock - call

        annualized = (1 + total_return/cost_base) ** (365/expiry_days) - 1
        
        return annualized

# d = DataDAO(DataProcessor())
# for ticker, financials in d.stock_data.items():
#     print(f"\n{ticker}")
#     for key, data in financials.items():
#         print(f"\n{key}")
#         print(d.stock_data[ticker][key])

