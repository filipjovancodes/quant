from src.option_position import OptionPosition
from src.stock_position import StockPosition
from yahoo_fin import stock_info as si


class Strategy:
    def __init__(self, stock: StockPosition = None, option: OptionPosition = None) -> None:
        self.stock = stock
        self.option = option

    def market_value(self, end_currency = None) -> float:
        total = 0
        if self.stock is not None:
            total += self.stock.market_value(end_currency)
        if self.option is not None:
            total += self.option.market_value(end_currency)

        return total

    def pnl(self, end_currency = None) -> float:
        total = 0
        if self.stock is not None:
            total += self.stock.pnl(end_currency)
        if self.option is not None:
            total += self.option.pnl(end_currency)

        return total
    
    def annualized_return(self) -> float:
        annualized = 0

        if self.stock is None and self.option is None:
            print("ERROR: Cannot compute annualized return for empty strategy")
            exit(1)
        
        elif self.stock is None: # TODO compute return for pure option play -> spy puts
            return 0

        elif self.option is None: # TODO handle currency conversion -> GRVY KRW -> USD
            # for bond assets return yield
            if self.stock.position.contract.symbol == "TLT":
                return self.stock.get_dividend_yield()

            stock_price = self.stock.get_price()

            # check if financials are in a different currency than the stock
            ticker = self.stock.get_ticker()
            stock_info = ticker.get_info()
            stock_currency = stock_info["currency"]
            financial_currency = stock_info["financialCurrency"]
            if stock_currency != financial_currency:
                currency_symbol = self.stock.yf_currency_symbol(stock_currency, financial_currency)
                exchange_rate = si.get_live_price(currency_symbol)
                stock_price *= exchange_rate

            share_issued = self.stock.get_share_issued()
            mcap = stock_price * share_issued

            cf = self.stock.get_cash_flow_avg()
    
            return cf / mcap
        
        else:
            expiry_days = self.option.days_to_expiry()
            dividend_return = self.option.option_dividend_return()
            
            call = float(self.option.price)/100
            stock = float(self.stock.price)
            strike = self.option.position.contract.strike
            
            call_return = call + strike - stock
            total_return = call_return + dividend_return
            cost_base = stock - call

            annualized = (1 + total_return/cost_base) ** (365/expiry_days) - 1
        
        return annualized


    def __str__(self) -> str:
        str = "Strategy:\n"
        str += f"Stock: {self.stock}\n"
        str += f"Option: {self.option}\n"
        return str