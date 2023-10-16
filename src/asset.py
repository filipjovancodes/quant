import math
from dateutil.relativedelta import relativedelta
from datetime import datetime
from ib_insync import *
from yahoo_fin import stock_info as si
from yahoo_fin import options as op
import yfinance as yf


class Asset:
    def __init__(self, ticker):
        self.ticker = ticker

    # def market_value(self, end_currency = None) -> float:
    #     exchange_rate = 1
    #     currency = self.position.contract.currency
    #     if end_currency is not None and currency != "CAD":
    #         currency_symbol = self.yf_currency_symbol(currency, "CAD")
    #         exchange_rate = si.get_live_price(currency_symbol)

    #     return self.price * exchange_rate * self.position.position

    # def pnl(self, end_currency = None) -> float:
    #     exchange_rate = 1
    #     currency = self.position.contract.currency
    #     if end_currency is not None and currency != "CAD":
    #         currency_symbol = self.yf_currency_symbol(currency, "CAD")
    #         exchange_rate = si.get_live_price(currency_symbol)

    #     return (self.price - self.position.avgCost) * exchange_rate * self.position.position
    
    def yf_currency_symbol(self, numerator, denominator) -> str:
        if numerator == "USD":
            return denominator + "=X"
        
        return numerator + denominator + "=X"
    
    # def yf_symbol(self) -> str:
    #     symbol = self.position.contract.symbol
    #     exchange = self.position.contract.exchange

    #     s = symbol.replace(".", "-")
    #     if exchange == "TSE":
    #         s += ".TO"
    #     elif exchange == "VENTURE":
    #         s += ".V"
    #     elif exchange == "LSE":
    #         s += ".L"
    #     elif symbol == "MCD" or symbol == "M6B":
    #         s += "=F"
    #     return s

    def format_percentage(self, percent: str) -> float:
        percent = percent.removesuffix("%")
        return float(percent)/100
    
    def get_option_chain_row(self, symbol: str, right: str, strike: float, contractDate: str):
        optionType = "calls" if right == "C" else "puts"
        options_chain = op.get_options_chain(symbol, contractDate)[optionType]

        return options_chain.loc[options_chain["Strike"] == strike] 

    def get_option_chain_item(self, symbol: str, right: str, strike: float, contractDate: str, column: str):
        option = self.get_option_chain_row(symbol, right, strike, contractDate)

        result = option.iloc[0][column]

        if column == "Implied Volatility":
            result = self.format_percentage(result)

        return result

    def get_option_iv(self, symbol: str, right: str, strike: float, contractDate: str) -> float:
        return self.get_option_chain_item(symbol, right, strike, contractDate, "Implied Volatility")

    def get_option_price(self, symbol: str, right: str, strike: float, contractDate: str) -> float:
        option = self.get_option_chain_row(symbol, right, strike, contractDate)

        bid = option.iloc[0]["Bid"]
        ask = option.iloc[0]["Ask"]
        if bid != 0 and ask != 0:
            return bid + (ask - bid) / 2
        
        return option.iloc[0]["Last Price"]

    # get price of stock given symbol. ex. 'AAPL'
    def get_price_asset(self, symbol: str):
        return si.get_live_price(symbol)

    def get_price(self):
        # if contract.exchange == "LSE":
        #     last /= 100

        # if isinstance(contract, Option):
        #     last = self.get_option_price(
        #         assetSymbol, 
        #         contract.right, 
        #         contract.strike, 
        #         contract.lastTradeDateOrContractMonth
        #     ) * float(contract.multiplier)

        return self.get_price_asset(self.ticker)

    # def get_option_greeks(self) -> OptionComputation:
    #     contract = self.position.contract
    #     #  Skip CGX (TSE) option contract since yahoo finance does not have option data
    #     if isinstance(contract, Option) and contract.symbol == "CGX":
    #         return -1
        
    #     assetSymbol = self.yf_symbol()
    #     last = self.get_price_asset(assetSymbol)

    #     impliedVolatility = self.get_option_iv(
    #         assetSymbol, 
    #         contract.right, 
    #         contract.strike, 
    #         contract.lastTradeDateOrContractMonth
    #     )

    #     updatedContract = Contract(
    #         conId= contract.conId,
    #         symbol= contract.symbol,
    #         exchange= "CBOE",
    #         lastTradeDateOrContractMonth= contract.lastTradeDateOrContractMonth,
    #         strike= contract.strike,
    #         right= contract.right,
    #         multiplier= contract.multiplier,
    #         currency= contract.currency,
    #         localSymbol= contract.localSymbol,
    #         tradingClass= contract.tradingClass
    #     )

    #     return self.ib.calculateOptionPrice(updatedContract, impliedVolatility, last)
    
    def get_ticker(self):
        return yf.Ticker(self.ticker)
    
    def get_cash_flow_avg(self):
        ticker = self.get_ticker()
        cf = ticker.cash_flow

        return cf.loc["Free Cash Flow"].mean()
    
    def get_net_debt(self):
        ticker = self.get_ticker()
        bs = ticker.quarterly_balance_sheet

        ca = bs.loc["Current Assets"].iloc[0]

        try:
            td = bs.loc["Total Debt"].iloc[0]
        except KeyError:
            td = bs.loc["Total Liabilities Net Minority Interest"].iloc[0]

        return ca - td

    def get_share_issued(self):
        ticker = self.get_ticker()
        bs = ticker.quarterly_balance_sheet

        return bs.loc["Share Issued"].iloc[0]
    
    def get_intrinsic_value(self):
        cf_avg = self.get_cash_flow_avg()
        net_debt = self.get_net_debt()

        valuation = cf_avg * 10
        lv = net_debt + valuation

        stock_price = self.get_price()
        share_issued = self.get_share_issued()
        mcap = stock_price * share_issued
        share_lv = lv / mcap * stock_price

        return share_lv
    
    def get_dividend_yield(self) -> float:
        # get dividends over the last year
        # common: 4, 12 process as such else weird and flag and handle later
        dividends = si.get_dividends(self.ticker)

        d = datetime.now()
        d = d.replace(year = d.year - 1)

        print(dividends)
        print(d)

        dividends_last_year = dividends[dividends.index.to_pydatetime() > d]

        if len(dividends_last_year) == 0:
            return 0

        print(dividends_last_year)
        recent_dividend = dividends_last_year.iloc[-1]["dividend"]

        return recent_dividend * len(dividends_last_year) / self.get_price()
    
    def get_pe(self) -> float:
        table = si.get_quote_table(self.ticker)

        return table["PE Ratio (TTM)"]
    
    def get_dividend_yield_simple(self) -> float:
        table = si.get_quote_table(self.ticker)

        return float(table["Forward Dividend & Yield"].split("(")[1].split("%")[0])/100
    
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
    
    # input net debt per share and price per share
    def get_option(self, nd, price):
        if nd > price:
            nd = price * 0.9

        d = datetime.now()
        target_expiry = d + relativedelta(months = 6)
        target_strike = math.floor(nd)

        max_itr_days = 100
        i = 0
        option = None
        while i < max_itr_days:
            date_prev = target_expiry + relativedelta(days = i)
            date_prev = self.format_date(year = date_prev.year, month = date_prev.month, day = date_prev.day)
            date_next = target_expiry - relativedelta(days = i)
            date_next = self.format_date(year = date_next.year, month = date_next.month, day = date_next.day)
            expiries = [date_prev, date_next]
            
            for expiry in expiries:
                try:
                    calls = op.get_options_chain(self.ticker, expiry)["calls"]
                    strikes = calls["Strike"].values

                    max_itr_strike = 100
                    j = 0
                    while j < max_itr_strike:
                        strike_check = [target_strike - 0.5 * j, target_strike + 0.5 * j]
                        for strike in strike_check:
                            if strike in strikes:
                                target_strike = strike
                                j = max_itr_strike
                                break
                        j += 1

                    print(target_expiry, target_strike)

                    target_expiry = expiry
                    i = max_itr_days
                    break

                except:
                    pass

            i += 1

        print(target_expiry, target_strike)

                

                

            