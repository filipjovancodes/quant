import traceback
from ib_insync import IB, Position
from data_dao import DataDAO
from src.strategy import Strategy
from src.strategy_builder import StrategyBuilder


# TODO figure out how to handle positions in multiple accounts -> TLT in TFSA and Margin
# TODO figure out why same account positions repeat some time -> SPY twice
# TODO more accurate option pricing rather than just pulling from yahoo finance
# TODO MCD, M6B, CGX pricing
class Portfolio:
    def __init__(self, ib: IB):
        self.ib = ib
        self.data_dao = DataDAO()
        self.strategies = {} # {str : Strategy}

    def add_strategy(self, position: Position) -> None:
        account = position.account
        symbol = position.contract.symbol

        if account not in self.strategies:
            self.strategies[account] = {}

        if symbol not in self.strategies[account]:
            self.strategies[account][symbol] = StrategyBuilder(self.ib, self.data_dao)
        self.strategies[account][symbol].add_position(position)

    def build_strategies(self):
        for account, account_dict in self.strategies.items():
            for symbol, strategy in account_dict.items():
                self.strategies[account][symbol] = self.strategies[account][symbol].build_strategy()

    def print_core(self):
        for account, account_dict in self.strategies.items():
            total_portfolio, total_pnl, total_return = 0, 0, 0
            for symbol, strategy in account_dict.items():
                try:
                    market_value = strategy.market_value("CAD")
                    pnl = strategy.pnl("CAD")
                    annualized_return = strategy.annualized_return()

                    print(f"\nSymbol: {symbol}")
                    print(f"Market Value (CAD): {market_value}")
                    print(f"PNL (CAD): {pnl}")
                    print(f"Expected Return: {annualized_return * market_value}")
                    print(f"Annualized: {annualized_return * 100}%")

                    total_portfolio += market_value
                    total_pnl += pnl
                    total_return += annualized_return * market_value
                except:
                    print(traceback.format_exc())

            print(f"\nAccount {account}")
            print(f"Total Portfolio: {total_portfolio}")
            print(f"Total PNL: {total_pnl}")
            print(f"Expected Return: {total_return}")
            print(f"Annualized: {(total_return / total_portfolio) * 100}%")
            print(f"Monthly: {total_return / 12}")
            print(f"Daily: {total_return / 365}")

    def __str__(self):
        str = "StrategyCongregator:\n"
        for account, account_dict in self.strategies.items():
            str += f"\nAccount: {account}\n"
            for symbol, strategy in account_dict.items():
                str += f"Symbol: {symbol}\n"
                str += f"Strategy: {strategy}\n"
        return str

