from ib_insync import Position
from src.strategy import Strategy
from data_dao import DataDAO


class CoveredCall(Strategy):
    def __init__(self, position_list: list[Position], position_map: {}, data_dao: DataDAO):
        super().__init__(position_list, position_map, data_dao)
        self.position_list = position_list
        self.stock = position_list[position_map["Stock"][1]]
        self.call = position_list[position_map["Call"][1]]

    def annualized_return(self):  
        pass