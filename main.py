from ib_insync import *

from src.option_position import OptionPosition
from src.stock_position import StockPosition
from src.strategy_congregator import StrategyCongregator


ib = IB()
ib.connect('127.0.0.1', 7496, clientId=1, readonly=True)

ib.reqMarketDataType(3)
account_list = ib.managedAccounts()

# asset_position = AssetPosition(ib)

strategy_congregator = StrategyCongregator()

for account in account_list:
    # position_list = ib.positions(account)
    position_list = ib.positions("U5732481")

    for position in position_list:
        # TODO add futures to strategy -> could just handle futures completely separately -> all we need is total USD portfolio
        # TODO figure out how to handle CGX
        if position.contract.symbol != "CGX" and not isinstance(position.contract, Future):
            print(position)

            if isinstance(position.contract, Option):
                strategy_congregator.add_option(OptionPosition(ib, position))
            else:
                strategy_congregator.add_stock(StockPosition(ib, position))


print(strategy_congregator)

strategy_congregator.print_core()


# TODO serialize congregator -> use json

# TODO
# prioritize aggregating core data for all tickers into a csv and updating it semi regularly then pull data from that csv instead of through api calls
# what to do about yahoo finance IV being inconsistent? -> own pricing model?
# create output data file that has information needed for option trading strategy readily available -> this way won't need to make api calls and the screener will be much faster -> 
# why is get_dividends not returning the last two years?
# Scanner: search high intrinsic value high cashflow and high standard deviation -> slow because of yahoo finance web scrape call -> run every day after market close and use that number as share price -> how to run schedule?
# DCF: Take average of last 5 years cashflow, project at +2% terminal, wacc 12% - Intrinsic Value: Current assets - liabilities + leases -> DCF is expected return, stdev of cashflows last 5 years is risk -> Where to get more years financial data?
# Analyze options chain: compare delta and return -> when to do 0.75 delta vs 0.9? When to choose longer date vs shorter? Risk and Liquidity
# Notify when to update futures and quantity: future expiry date, total currency amount (non cad)
# Notify when to roll: delta < 0.6? -> do some analysis
# Create a bunch of virtual portfolios and track them. For each virtual portfolio use different metrics and track which ones perform best 
# Model strategies: stock, stock + itm call, stock + otm call, put
