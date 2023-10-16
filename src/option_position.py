from datetime import datetime
from ib_insync import *
from yahoo_fin import stock_info as si

from src.asset_position import AssetPosition


class OptionPosition(AssetPosition):
    def __init__(self, ib,  position: Position) -> None:
        super().__init__(ib)
        self.position = position
        self.greeks = self.get_option_greeks()
        self.price = self.get_price()
    
    def days_to_expiry(self) -> int:
        date = self.position.contract.lastTradeDateOrContractMonth
        diff = datetime.strptime(date, '%Y%m%d') - datetime.now()

        return diff.days
    
    def option_dividend_return(self) -> float:
        # get dividends over the last year
        # common: 4, 12 process as such else weird and flag and handle later
        dividends = si.get_dividends(self.position.contract.symbol)

        if len(dividends) == 0:
            return 0

        d = datetime.now()
        d = d.replace(year = d.year - 1)

        dividends_last_year = dividends[dividends.index.to_pydatetime() > d]
        dividend_days = 365/len(dividends_last_year)
        days_since_last_dividend = (datetime.now() - dividends_last_year.index.to_pydatetime()[-1]).days
        days_to_next_dividend = dividend_days - days_since_last_dividend

        if self.days_to_expiry() < days_to_next_dividend:
            return 0
        
        dividend_count = (self.days_to_expiry() - days_to_next_dividend) // dividend_days + 1
        recent_dividend = dividends_last_year.iloc[-1]["dividend"]

        return recent_dividend * dividend_count
    
    def __str__(self) -> str:
        str = "OptionPosition:\n"
        str += f"Position: {self.position}\n"
        str += f"Greeks: {self.greeks}\n"
        str += f"Price: {self.price}\n"
        return str