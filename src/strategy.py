from abc import ABC, abstractmethod
from ib_insync import Position
from data_dao import DataDAO
import utils.yf_utils as yf_utils


class Strategy(ABC):
    def __init__(self, position_list: list[Position], position_map: {}, data_dao: DataDAO):
        self.position_list = position_list
        self.position_map = position_map
        self.data_dao = data_dao

    @abstractmethod
    def pnl(self, end_currency = None) -> float:
        pass

    @abstractmethod
    def market_value(self, end_currency = None) -> float:
        pass
    
    @abstractmethod
    def annualized_return(self):
        pass
    