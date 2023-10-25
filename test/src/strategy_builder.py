from collections import defaultdict
from ib_insync import Position
from data_dao import DataDAO
from src.covered_call_strategy import CoveredCall


class StrategyBuilder:
    def __init__(self, data_dao: DataDAO):
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
            and counter["Call"][0] == 1
            and counter["Put"][0] == 0):
           return CoveredCall(self.position_list, counter, self.data_dao)
        # .... more strategies ....
        pass
