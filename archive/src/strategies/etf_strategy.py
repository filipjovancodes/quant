from ib_insync import IB, Position
from src.strategy import Strategy
from data_dao import DataDAO


class ETFStrategy(Strategy):
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
        return 0.08