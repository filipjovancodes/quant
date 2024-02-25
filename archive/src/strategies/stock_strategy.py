from ib_insync import IB, Position
from src.strategy import Strategy
from archive.data_dao import DataDAO


class StockStrategy(Strategy):
    def __init__(self, position_list: list[Position], position_map: {}, data_dao: DataDAO, ib: IB):
        self.ib = ib
        self.position_list = position_list
        self.data_dao = data_dao
        self.stock = position_list[position_map["Stock"][1]]

    def pnl(self, end_currency = None) -> float:
        exchange_rate = self.data_dao.get_exchange_rate(self.stock.contract.currency, end_currency)
        return (self.data_dao.get_stock_price(self.stock.contract.symbol) - self.stock.avgCost) * self.stock.position * exchange_rate
    
    def market_value(self, end_currency = None) -> float:
        exchange_rate = self.data_dao.get_exchange_rate(self.stock.contract.currency, end_currency)
        return self.data_dao.get_stock_price(self.stock.contract.symbol) * self.stock.position * exchange_rate

    def annualized_return(self):
        ticker = self.stock.contract.symbol
        cf_avg = self.data_dao.get_cashflow_avg(ticker)
        stock_price = self.data_dao.get_stock_price(ticker)
        share_issued = self.data_dao.get_share_issued(ticker)
        mcap = stock_price * share_issued
        return cf_avg / mcap