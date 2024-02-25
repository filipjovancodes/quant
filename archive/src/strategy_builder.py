from ib_insync import IB, Position
from archive.data_dao import DataDAO
from src.strategies.covered_call_strategy import CoveredCallStrategy
from src.strategies.etf_strategy import ETFStrategy
from src.strategies.put_strategy import PutStrategy
from src.strategies.stock_strategy import StockStrategy


class StrategyBuilder:
    def __init__(self, ib: IB, data_dao: DataDAO):
        self.ib = ib
        self.data_dao = data_dao
        self.position_list = []

    def add_position(self, position: Position):
        self.position_list.append(position)

    # TODO get position contract (Stock, Option, etc) and count amount then build strategy based on that
    # this object wont work because if there are multiple calls the index would change and we'd lose track of it
    def build_strategy(self):
        counter = {}
        counter["Stock"] = [0, 0]
        counter["Call"] = [0, 0]
        counter["Put"] = [0, 0]

        for i, position in enumerate(self.position_list):
            contract_string = position.contract.__class__.__name__
            if contract_string == "Option":
                contract_string = "Call" if position.contract.right == "C" else "Put"
            counter[contract_string][0] += 1
            counter[contract_string][1] = i

        if (counter["Stock"][0] == 1
            and counter["Call"][0] == 0
            and counter["Put"][0] == 0):
            ticker = self.position_list[0].contract.symbol
            if ticker in self.data_dao.stock_data and self.data_dao.stock_data[ticker]["info"]["quoteType"] == "ETF":
                return ETFStrategy(self.position_list, counter, self.data_dao, self.ib)
            else:
                return StockStrategy(self.position_list, counter, self.data_dao, self.ib)
        
        elif (counter["Stock"][0] == 1
            and counter["Call"][0] == 1
            and counter["Put"][0] == 0):
           return CoveredCallStrategy(self.position_list, counter, self.data_dao, self.ib)
        
        elif (counter["Stock"][0] == 0
            and counter["Call"][0] == 0
            and counter["Put"][0] == 1):
           return PutStrategy(self.position_list, counter, self.data_dao, self.ib)
        # .... more strategies ....
        pass
