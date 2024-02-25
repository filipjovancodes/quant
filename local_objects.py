# Define a class to represent option chain data for a single expiry
import jsonpickle


class OptionPosition:
    def __init__(
        self,
        ticker,
        # symbol,
        # stockPrice,
        # optionPrice,
        # strike,
        # expiry,
        # dividend,
        # dividendPeriods,
        # delta,
        # theta,
        # gamma,
        # vega,
    ):
        self.symbol = ticker.contract.symbol
        stock_price = yfinance.Ticker(stock_symbol).fast_info["lastPrice"]
        # TODO when ibkr fixes their shit change this
        # self.stockPrice = ticker.modelGreeks.undPrice
        self.stockPrice = stock_price
        self.bidSize = ticker.bidSize
        self.bid = ticker.bid
        self.ask = ticker.ask
        self.askSize = ticker.askSize
        self.optionPrice = ticker.modelGreeks.optPrice
        self.strike = ticker.contract.strike
        self.expiry = ticker.contract.lastTradeDateOrContractMonth
        self.dividend = 0
        self.dividendPeriods = 0
        self.dividendReturn = self.get_option_dividend_return()
        self.delta = ticker.modelGreeks.delta
        self.theta = ticker.modelGreeks.theta
        self.gamma = ticker.modelGreeks.gamma
        self.vega = ticker.modelGreeks.vega

    def callReturn(self):
        if self.strike < self.stockPrice:
            return self.strike + self.optionPrice - self.stockPrice
        else:
            return self.optionPrice

    def totalReturn(self):
        return self.callReturn() + self.dividendReturn

    def costBase(self):
        return self.stockPrice - self.optionPrice

    def daysToExpiry(self):
        return (datetime.strptime(self.expiry, "%Y%m%d") - datetime.now()).days

    def annualized(self):
        return (1 + self.totalReturn() / self.costBase()) ** (
            365 / self.daysToExpiry()
        ) - 1

    def protection(self):
        return 1 - self.costBase() / self.stockPrice

    def breakEven(self):
        return self.costBase() - self.dividendReturn
    
    def get_option_dividend_return(self) -> float:
        # TODO handle volatile dividends
        dividends = self.get_dividends().tz_convert("UTC")

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

        if self.daysToExpiry() < days_to_next_dividend:
            return 0

        dividend_count = (self.daysToExpiry() - days_to_next_dividend) // dividend_days + 1
        recent_dividend = dividends_last_year.iloc[-1]

        self.dividend = recent_dividend
        self.dividendPeriods = dividend_count

        return recent_dividend * dividend_count
    
    def get_dividends(self):
        # Execute the SELECT statement to retrieve dividend information for the given ticker
        stock_data = self.get_stock(self.symbol)
        return stock_data.dividends
    
    def get_stock(self, symbol):
        conn = sqlite3.connect("main.db")
        cursor = conn.cursor()

        rows = cursor.execute(f"SELECT * FROM Stocks WHERE symbol = ?", (symbol,)).fetchone()

        conn.close()
        return jsonpickle.decode(rows[1])
    
    def __repr__(self):
        return (f"TickerData(symbol={self.symbol}, stockPrice={self.stockPrice}, "
                f"bidSize={self.bidSize}, bid={self.bid}, ask={self.ask}, "
                f"askSize={self.askSize}, optionPrice={self.optionPrice}, "
                f"strike={self.strike}, expiry={self.expiry}, dividend={self.dividend}, "
                f"dividendPeriods={self.dividendPeriods}, dividendReturn={self.dividendReturn}, "
                f"delta={self.delta}, theta={self.theta}, gamma={self.gamma}, "
                f"vega={self.vega})")


class OptionChainList:
    def __init__(self):
        self.option_chain_list = []

class OptionChainSingle:
    def __init__(self, calls, puts, underlying):
        self.calls = calls
        self.puts = puts
        self.underlying = underlying


# Define a class to represent option chain data for multiple expiries
class OptionChainMultipleObject:
    def __init__(self):
        self.option_chain = {}

    def add_chain(self, expiry, calls, puts, underlying):
        self.option_chain[expiry] = OptionChainSingle(calls, puts, underlying)

    def get_chain(self, expiry):
        return self.option_chain[expiry]


class OptionData:
    def __init__(
        self,
        conId,
        symbol,
        expiry,
        strike,
        right,
        exchange,
        optPrice,
        undPrice,
        impliedVol,
        delta,
        gamma,
        vega,
        theta,
    ):
        self.conId = conId
        self.symbol = symbol
        self.expiry = expiry
        self.strike = strike
        self.right = right
        self.exchange = exchange
        self.optPrice = optPrice
        self.undPrice = undPrice
        self.impliedVol = impliedVol
        self.delta = delta
        self.gamma = gamma
        self.vega = vega
        self.theta = theta

    def __repr__(self):
        return (
            f"OptionLocal(conId={self.conId}, symbol={self.symbol}, "
            f"expiry={self.expiry}, strike={self.strike}, right={self.right}, "
            f"exchange={self.exchange}, optPrice={self.optPrice}, undPrice={self.undPrice}, "
            f"impliedVol={self.impliedVol}, delta={self.delta}, gamma={self.gamma}, "
            f"vega={self.vega}, theta={self.theta})"
        )

class PositionData:
    def __init__(self, contract, position, avgCost):
        self.contract=contract
        self.position=position
        self.avgCost=avgCost

    def __repr__(self):
        return f"PositionData(contract={self.contract}, position={self.position}, avgCost={self.avgCost})"

class StockData:
    def __init__(self, info, financials, balanceSheet, cashFlow, dividends, fast_info, option_chain):
        self.info = info
        self.financials = financials
        self.balanceSheet = balanceSheet
        self.cashFlow = cashFlow
        self.dividends = dividends
        self.fast_info = fast_info
        self.option_chain = option_chain
    
    def __repr__(self):
        return (f"StockData(symbol={self.info['symbol']})")

class CoveredCallStrategyObject:
    # object for db serialization since dao cannot be serialized
    def __init__(self, stock_position, option_position):
        self.stock_position = stock_position
        self.option_position = option_position

class PutHedgeStrategyObject:
     # object for db serialization since dao cannot be serialized
    def __init__(self, option_position):
        self.option_position = option_position   

class LongStockStrategyObject:
     # object for db serialization since dao cannot be serialized
    def __init__(self, stock_position):
        self.stock_position = stock_position

class CurrencyHedgeStrategyObject:
    # object for db serialization since dao cannot be serialized
    def __init__(self, future_position):
        self.future_position = future_position

class CashStrategyObject:
    # object for db serialization since dao cannot be serialized
    def __init__(self, cash_balance):
        self.cash_balance = cash_balance  

class CoveredCallStrategy:
    def __init__(self, dao, stock_position, option_position):
        self.dao = dao
        self.stock_position = stock_position
        self.option_position = option_position
        self.stock_details = self.dao.get_stock(self.stock_position.contract.symbol)
        self.option_details = self.dao.get_option(self.option_position.contract.conId)

    def symbol(self):
        return self.stock_position.contract.symbol

    def stock_exposure(self):
        return self.stock_details.fast_info["lastPrice"] * self.quantity() * self.exchangeRateCAD()
    
    def option_exposure(self):
        return self.option_details.optPrice * self.quantity() * self.exchangeRateCAD()

    def netPrice(self):
        return self.stock_details.fast_info["lastPrice"] - self.option_details.optPrice
    
    def quantity(self):
        return self.stock_position.position
    
    def annualized(self):
        if self.symbol() == "VTI":
            return 0.08
        return self.dao.get_option_annualized(self.option_details, self.stock_details.fast_info["lastPrice"])
    
    def exchangeRateCAD(self):
        if self.stock_position.contract.currency == "USD":
            return self.dao.get_currency()
        return 1
    
    def totalCAD(self):
        return self.netPrice() * self.quantity() * self.exchangeRateCAD()
    
    def returnCAD(self):
        return self.totalCAD() * self.annualized()
        
    def sector(self):
        return self.stock_details.info["sector"] if "sector" in self.stock_details.info else ""
        
    def industry(self):
        return self.stock_details.info["industry"] if "industry" in self.stock_details.info else ""

    # TODO calculate on own 
    def beta(self):
        return self.stock_details.info["beta"] if "beta" in self.stock_details.info else 1
    
    # TODO this is wrong because it should be delta on option price not delta on netPrice
    def delta(self):
        return 1 - self.option_details.delta
    
    def theta(self):
        return 0 - self.option_details.theta
    
    def gamma(self):
        return 0 - self.option_details.gamma
    
    def vega(self):
        return 0 - self.option_details.vega
        
    def expiry(self):
        return self.option_position.contract.lastTradeDateOrContractMonth

    def get_share_issued(self):
        return self.stock_details.balanceSheet.loc["Share Issued"].iloc[0]
    
    def get_stock_price(self):
        return self.stock_details.fast_info["lastPrice"]

    def get_total_debt(self):
        bs = self.stock_details.balanceSheet
        try:
            td = bs.loc["Total Debt"].iloc[0]
        except KeyError:
            td = bs.loc["Total Liabilities Net Minority Interest"].iloc[0]
        return td

    def get_total_equity(self):
        return self.stock_details.balanceSheet.loc["Total Equity Gross Minority Interest"].iloc[0]
    
    def get_current_assets(self):
        return self.stock_details.balanceSheet.loc["Current Assets"].iloc[0]

    def get_net_debt(self):
        return self.get_current_assets() - self.get_total_debt() 

    def get_cashflow_avg(self):
        return self.stock_details.cashFlow.loc["Free Cash Flow"].mean()

    def get_eps(self):
        return self.stock_details.financials.loc["Basic EPS"].iloc[0]
    
    def get_pe(self):
        return (self.get_stock_price() / self.get_eps())

    def get_dcf_stock_price(self, cashflow, net_debt, stock_price, share_issued):
        valuation = cashflow * 10
        lv = net_debt + valuation

        mcap = stock_price * share_issued
        share_iv = lv / mcap * stock_price

        return share_iv

    def get_liquid_stock_price(self, stock_price, market_cap, net_debt):
        return net_debt / market_cap * stock_price

    def valuation_values(self):
        if self.symbol() == "VTI":
            return []

        symbol = self.symbol()
        share_issued = self.get_share_issued()
        stock_price = self.get_stock_price()
        market_cap = share_issued * stock_price # Market cap
        # net_debt = self.get_net_debt()
        total_equity = self.get_total_equity()
        cashflow = self.get_cashflow_avg()
        pe = self.get_pe()
        eps = self.get_eps()
        # intrinsic_value = self.get_dcf_stock_price(cashflow, net_debt, stock_price, share_issued)
        # liquid_stock = self.get_liquid_stock_price(stock_price, market_cap, net_debt)
        intrinsic_value = self.get_dcf_stock_price(cashflow, total_equity, stock_price, share_issued)
        liquid_stock = self.get_liquid_stock_price(stock_price, market_cap, total_equity)
        
        return [
            symbol,
            round(stock_price, 2),
            round(share_issued / 1000000, 2),
            round(market_cap / 1000000, 2),
            # round(net_debt / 1000000, 2),
            round(total_equity / 1000000, 2),
            round(cashflow / 1000000, 2),
            round(pe, 2),
            round(eps, 2),
            round(intrinsic_value, 2),
            round(liquid_stock, 2)
        ]

    def __repr__(self):
        return f"CoveredCallStrategy(stock_position={self.stock_position}, option_position={self.option_position}), stock_details={self.stock_details}, option_details={self.option_details})"

class PutHedgeStrategy:
    def __init__(self, dao, option_position):
        self.dao = dao
        self.option_position = option_position
        self.stock_details = self.dao.get_stock(self.option_position.contract.symbol)
        self.option_details = self.dao.get_option(self.option_position.contract.conId)

    def symbol(self):
        return self.option_position.contract.symbol
    
    def stock_exposure(self):
        return self.stock_details.fast_info["lastPrice"] * self.quantity() * self.exchangeRateCAD()
    
    def option_exposure(self):
        return self.option_details.optPrice * self.quantity() * self.exchangeRateCAD()

    def netPrice(self):
        return self.option_details.optPrice * 100
    
    def quantity(self):
        return self.option_position.position
    
    def annualized(self):
        return -1
    
    def exchangeRateCAD(self):
        if self.option_position.contract.currency == "USD":
            return self.dao.get_currency()
        return 1
    
    def totalCAD(self):
        return self.netPrice() * self.quantity() * self.exchangeRateCAD()
    
    def returnCAD(self):
        return self.totalCAD() * self.annualized()
        
    def sector(self):
        return self.stock_details.info["sector"] if "sector" in self.stock_details.info else ""
        
    def industry(self):
        return self.stock_details.info["industry"] if "industry" in self.stock_details.info else ""
    
    def beta(self):
        return self.stock_details.info["beta"] if "beta" in self.stock_details.info else 1
        
    def delta(self):
        return self.option_details.delta
    
    def theta(self):
        return self.option_details.theta
    
    def gamma(self):
        return self.option_details.gamma
    
    def vega(self):
        return self.option_details.vega

    def expiry(self):
        return self.option_position.contract.lastTradeDateOrContractMonth

class LongStockStrategy:
    def __init__(self, dao, stock_position):
        self.dao = dao
        self.stock_position = stock_position
        self.stock_details = self.dao.get_stock(self.stock_position.contract.symbol)

    def symbol(self):
        return self.stock_position.contract.symbol

    def stock_exposure(self):
        return self.stock_details.fast_info["lastPrice"] * self.quantity() * self.exchangeRateCAD()
    
    def option_exposure(self):
        return 0

    def netPrice(self):
        return self.stock_details.fast_info["lastPrice"]
    
    def quantity(self):
        return self.stock_position.position
    
    def annualized(self):
        # TODO cf / mcap for stocks
        if self.symbol() == "SGOV":
            return self.dao.get_rfr()
        return 0.08
    
    def exchangeRateCAD(self):
        if self.stock_position.contract.currency == "USD":
            return self.dao.get_currency()
        return 1
    
    def totalCAD(self):
        return self.netPrice() * self.quantity() * self.exchangeRateCAD()
    
    def returnCAD(self):
        return self.totalCAD() * self.annualized()
        
    def sector(self):
        return self.stock_details.info["sector"] if "sector" in self.stock_details.info else ""
        
    def industry(self):
        return self.stock_details.info["industry"] if "industry" in self.stock_details.info else ""
    
    def beta(self):
        if self.symbol() == "SGOV":
            return 0
        return self.stock_details.info["beta"] if "beta" in self.stock_details.info else 1
    
    def delta(self):
        if self.symbol() == "SGOV":
            return 0
        return 1
    
    def theta(self):
        return 0
    
    def gamma(self):
        return 0
    
    def vega(self):
        return 0

    def expiry(self):
        return ""
  
class CurrencyHedgeStrategy:
    def __init__(self, dao, future_position):
        self.dao = dao
        self.future_position = future_position
    
    def symbol(self):
        return self.future_position.contract.symbol
    
    def stock_exposure(self):
        return 0
    
    def option_exposure(self):
        return 0

    def netPrice(self):
        return self.dao.get_futures_price() * 10000 - self.future_position.avgCost
    
    def quantity(self):
        return self.future_position.position
    
    def annualized(self):
        return 0
    
    def totalCAD(self):
        return self.netPrice() * self.quantity()
    
    def returnCAD(self):
        return self.totalCAD()
        
    def sector(self):
        return ""
        
    def industry(self):
        return ""

    def beta(self):
        return 0
    
    def delta(self):
        return 0
    
    def theta(self):
        return 0
    
    def gamma(self):
        return 0
    
    def vega(self):
        return 0
   
    def expiry(self):
        return self.future_position.contract.lastTradeDateOrContractMonth

class CashStrategy:
    def __init__(self, dao, cash_balance):
        self.dao = dao
        self.cash_balance = cash_balance
    
    def symbol(self):
        return "Cash"
    
    def stock_exposure(self):
        return 0
    
    def option_exposure(self):
        return 0

    def netPrice(self):
        return self.cash_balance
    
    def quantity(self):
        return self.cash_balance
    
    def annualized(self):
        return 0
    
    def totalCAD(self):
        return self.cash_balance
    
    def returnCAD(self):
        return 0
        
    def sector(self):
        return ""
        
    def industry(self):
        return ""
    
    def beta(self):
        return 0
    
    def delta(self):
        return 0
    
    def theta(self):
        return 0
    
    def gamma(self):
        return 0
    
    def vega(self):
        return 0
   
    def expiry(self):
        return ""

