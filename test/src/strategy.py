from abc import ABC, abstractmethod
from ib_insync import Position
from data_dao import DataDAO
import utils.yf_utils as yf_utils


class Strategy(ABC):
    def __init__(self, position_list: list[Position], position_map: {}, data_dao: DataDAO):
        self.position_list = position_list
        self.position_map = position_map
        self.data_dao = data_dao

    def pnl(self, end_currency = None) -> float:
        total = 0
        for position in self.position_list:
            exchange_rate = self.data_dao.get_exchange_rate(position.contract.currency, end_currency)
            total += (self.data_dao.get_stock_price(position.contract.symbol) - position.avgCost) * exchange_rate * position.position

        return total

    def market_value(self, end_currency = None) -> float:
        for position in self.position_list:
            exchange_rate = self.data_dao.get_exchange_rate(position.contract.currency, end_currency)
            return self.data_dao.get_stock_price(position.contract.symbol) * exchange_rate * position.position

    @abstractmethod
    def annualized_return(self):
        pass
    