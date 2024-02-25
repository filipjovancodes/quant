from abc import ABC, abstractmethod
from ib_insync import IB, Position
from archive.data_dao import DataDAO
import utils.yf_utils as yf_utils


class Strategy(ABC):
    def __init__(self, position_list: list[Position], position_map: {}, data_dao: DataDAO, ib: IB):
        self.ib = ib
        self.position_list = position_list
        self.position_map = position_map
        self.data_dao = data_dao
    
    def awaitGreeks(self, data):
        while data.modelGreeks is None:
            print("awaiting data for ", data.contract.localSymbol)
            self.ib.sleep(10)


    @abstractmethod
    def pnl(self, end_currency = None) -> float:
        pass

    @abstractmethod
    def market_value(self, end_currency = None) -> float:
        pass
    
    @abstractmethod
    def annualized_return(self):
        pass
    