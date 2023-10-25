import traceback
from ib_insync import Position
from src.strategy import Strategy
from data_dao import DataDAO


class CoveredCallStrategy(Strategy):
    def __init__(self, position_list: list[Position], position_map: {}, data_dao: DataDAO):
        self.position_list = position_list
        self.data_dao = data_dao
        self.stock = position_list[position_map["Stock"][1]]
        self.call = position_list[position_map["Call"][1]]

        # TODO refactor to ITM CC and OTM CC or CC to encompass both strats (probs with delta?)
        try:
            ticker = self.stock.contract.symbol
            stock_price = self.data_dao.get_stock_price(ticker)
            net_debt = self.data_dao.get_net_debt(ticker)
            self.option = self.data_dao.get_option(ticker, net_debt, stock_price)
            self.annualized = self.data_dao.get_option_annualized(self.option)
        except:
            print(traceback.format_exc())
            self.annualized = 0.08

    def pnl(self, end_currency = None) -> float:
        exchange_rate = self.data_dao.get_exchange_rate(self.stock.contract.currency, end_currency)
        stock_pnl = (self.data_dao.get_stock_price(self.stock.contract.symbol) - self.stock.avgCost) * self.stock.position * exchange_rate
        option_pnl = (self.option.option_price - self.call.avgCost) * self.call.position * exchange_rate
        return stock_pnl + option_pnl
    
    def market_value(self, end_currency = None) -> float:
        exchange_rate = self.data_dao.get_exchange_rate(self.stock.contract.currency, end_currency)
        stock_market_value = self.data_dao.get_stock_price(self.stock.contract.symbol) * self.stock.position * exchange_rate
        option_market_value = self.option.option_price * self.call.position * exchange_rate
        return stock_market_value + option_market_value

    def annualized_return(self):
        return self.annualized