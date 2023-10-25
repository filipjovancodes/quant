import math
import src.black_scholes as black_scholes
import src.option as option
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
        optionType = "calls" if right == "C" else "put"
        options_chain = op.get_options_chain(symbol, contractDate)[optionType]

        return options_chain.loc[options_chain["Strike"] == strike] 

    def get_option_chain_item(self, symbol: str, right: str, strike: float, contractDate: str, column: str):
        option = self.get_option_chain_row(symbol, right, strike, contractDate)

        result = option.iloc[0][column]

        if column == "Implied Volatility":
            result = self.format_percentage(result)

        return result

    def get_option_iv(self, symbol: str, right: str, strike: float, contractDate: str) -> float:
        iv = self.get_option_chain_item(symbol, right, strike, contractDate, "Implied Volatility")
        if iv < 0.05:
            price = self.get_option_price(symbol, right, strike, contractDate)
            days_to_expiry = (self.format_datetime(contractDate) - datetime.now()).days
            iv = black_scholes.implied_volatility(price, self.get_price(), strike, days_to_expiry/365, self.get_rate(), right)
        return iv

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

        dividends_last_year = dividends[dividends.index.to_pydatetime() > d]

        if len(dividends_last_year) == 0:
            return 0

        recent_dividend = dividends_last_year.iloc[-1]["dividend"]

        return recent_dividend * len(dividends_last_year) / self.get_price()
    
    def get_pe(self) -> float:
        table = si.get_quote_table(self.ticker)

        return table["PE Ratio (TTM)"]
    
    def get_dividend_yield_simple(self) -> float:
        table = si.get_quote_table(self.ticker)

        return float(table["Forward Dividend & Yield"].split("(")[1].split("%")[0])/100
    
    # TODO move to utils.format or something
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
    
    # TODO move to utils.format or something
    def format_datetime(self, date: str) -> datetime:
        return datetime(year = int(date[0:4]), month = int(date[4:6]), day = int(date[6:8]))
    
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

    def get_target_option(self, target_expiry, target_strike):
        result_expiry, result_strike = None, None
        max_itr_days = 100
        i = 0
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

                    result_strike = self.get_strike(target_strike, strikes)
                    result_expiry = expiry

                    i = max_itr_days
                    break

                except:
                    pass

            i += 1
        
        return result_expiry, result_strike
    
    def get_rate(self):
        return yf.Ticker("^IRX").info["open"]/100
    
    # input net debt per share and price per share
    def get_option(self, nd, price):
        if nd > price:
            nd = price * 0.9

        d = datetime.now()
        target_expiry = d + relativedelta(months = 6)
        target_strike = math.floor(nd)

        result_expiry, result_strike = self.get_target_option(target_expiry, target_strike)

        if result_expiry is None or result_strike is None:
            return option.Option()

        iv = self.get_option_iv(
            symbol = self.ticker,
            right = "C",
            strike = result_strike,
            contractDate = result_expiry
        )

        rate = self.get_rate()
        days_to_expiry = (self.format_datetime(result_expiry) - datetime.now()).days

        option_price, delta, gamma, vega, rho, theta = black_scholes.get_price_and_greeks(
            S = price,
            K = result_strike,
            T = days_to_expiry/365,
            r = rate,
            iv = iv,
            right = "C"
        )

        op = option.Option(
            ticker = self.ticker,
            right = "C",
            stock_price = price,
            strike = result_strike,
            expiry = result_expiry,
            rate = rate,
            iv = iv,
            option_price = option_price,
            delta = delta,
            gamma = gamma, 
            vega = vega,
            rho = rho, 
            theta = theta
        )

        return op
    
    # TODO refactor
    def option_dividend_return(self, days_to_expiry) -> float:
        # get dividends over the last year
        # common: 4, 12 process as such else weird and flag and handle later
        dividends = si.get_dividends(self.ticker)

        if len(dividends) == 0:
            return 0

        d = datetime.now()
        d = d.replace(year = d.year - 1)

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
    
    def get_option_annualized(self, option: option.Option):

        expiry_days = (self.format_datetime(option.expiry) - datetime.now()).days
        dividend_return = self.option_dividend_return(expiry_days)
        
        call = option.option_price
        stock = option.stock_price
        strike = option.strike
        
        call_return = call + strike - stock
        total_return = call_return + dividend_return
        cost_base = stock - call

        annualized = (1 + total_return/cost_base) ** (365/expiry_days) - 1
        
        return annualized
                

            