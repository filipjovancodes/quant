from ib_insync import IB, Position
from src.strategy import Strategy
from archive.data_dao import DataDAO


class PutStrategy(Strategy):
    def __init__(self, position_list: list[Position], position_map: {}, data_dao: DataDAO, ib: IB):
        self.ib = ib
        self.position_list = position_list
        self.data_dao = data_dao
        self.put = position_list[position_map["Put"][1]]

    def pnl(self, end_currency = None) -> float:
        exchange_rate = self.data_dao.get_exchange_rate(self.put.contract.currency, end_currency)
        return (self.data_dao.get_stock_price(self.put.contract.symbol) - self.put.avgCost) * exchange_rate * self.put.position
    
    def market_value(self, end_currency = None) -> float:
        exchange_rate = self.data_dao.get_exchange_rate(self.put.contract.currency, end_currency)
        return self.data_dao.get_stock_price(self.put.contract.symbol) * exchange_rate * self.put.position

    def annualized_return(self):
        return 0