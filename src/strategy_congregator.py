from src.option_position import OptionPosition
from src.strategy import Strategy
from src.stock_position import StockPosition


# TODO figure out how to handle positions in multiple accounts -> TLT in TFSA and Margin
# TODO figure out why same account positions repeat some time -> SPY twice
# TODO more accurate option pricing rather than just pulling from yahoo finance
# TODO MCD, M6B, CGX pricing
class StrategyCongregator:
    def __init__(self):
        self.strategies = {} # {str : Strategy}

    def add_stock(self, stock: StockPosition) -> None:
        symbol = stock.position.contract.symbol

        if symbol not in self.strategies:
            self.strategies[symbol] = Strategy()

        # if symbol in self.strategies and self.strategies[symbol].stock != None:
        #     print(f"ERROR: stock strategy already exists for {symbol}, exiting")
        #     exit(1)

        self.strategies[symbol].stock = stock

    def add_option(self, option: OptionPosition) -> None:
        contract = option.position.contract

        symbol = contract.symbol

        if symbol not in self.strategies:
            self.strategies[symbol] = Strategy()

        # if symbol in self.strategies and self.strategies[symbol].option != None:
        #     print(f"ERROR: option strategy already exists for {symbol}, exiting")
        #     exit(1)

        self.strategies[symbol].option = option

    def print_core(self):
        total_portfolio, total_pnl, total_return = 0, 0, 0
        for symbol, strategy in self.strategies.items():
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

        print(f"\nTotal Portfolio: {total_portfolio}")
        print(f"Total PNL: {total_pnl}")
        print(f"Expected Return: {total_return}")
        print(f"Annualized: {(total_return / total_portfolio) * 100}%")
        print(f"Monthly: {total_return / 12}")
        print(f"Daily: {total_return / 365}")

    def __str__(self):
        str = "StrategyCongregator:\n"
        for symbol, strategy in self.strategies.items():
            str += f"Symbol: {symbol}\n"
            str += f"Strategy: {strategy}\n"
        return str

