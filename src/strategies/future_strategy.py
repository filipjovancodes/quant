from ib_insync import Position
from src.strategy import Strategy
from data_dao import DataDAO

# TODO implement pnl -> parse Future and add to position_map, market_val -> download future data
class FutureStrategy(Strategy):
    def __init__(self, position_list: list[Position], position_map: {}, data_dao: DataDAO):
        self.position_list = position_list
        self.data_dao = data_dao
        self.future = position_list[position_map["Future"][1]]

    def pnl(self, end_currency = None) -> float:
        return 0
    
    def market_value(self, end_currency = None) -> float:
        return 0

    def annualized_return(self):
        return 0