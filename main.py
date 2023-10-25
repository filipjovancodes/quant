from ib_insync import *
from data_dao import DataDAO
from data_processor import DataProcessor

from src.portfolio import Portfolio


ib = IB()
ib.connect('127.0.0.1', 7496, clientId=1, readonly=True)

ib.reqMarketDataType(3)
account_list = ib.managedAccounts()

# asset_position = AssetPosition(ib)

data_processor = DataProcessor()
data_dao = DataDAO(data_processor)

portfolio = Portfolio(data_dao)

for account in account_list:
    position_list = ib.positions(account)

    for position in position_list:
        # TODO add futures to strategy -> could just handle futures completely separately -> all we need is total USD portfolio
        # TODO figure out how to handle CGX -> Options chain doesn't show on yahoo finance
        if position.contract.symbol != "CGX" and not isinstance(position.contract, Future):
            portfolio.add_strategy(position)

portfolio.build_strategies()

print(portfolio)

portfolio.print_core()


# TODO serialize congregator -> use json

# TODO
# Analyze portfolio exposure by sector/industry
# Manually add tickers to tickers and new_stock_data.pkl -> add canada tickers to tickers -> update tickers
# Manually add data to new_stock_data.pkl -> add cgx option manually
# Better option pricing and greeks model
# Scanner: search high intrinsic value high cashflow and high standard deviation -> slow because of yahoo finance web scrape call -> run every day after market close and use that number as share price -> how to run schedule?
# DCF: -> DCF is expected return, stdev of cashflows last 5 years is risk -> Where to get more years financial data?
# Analyze options chain: compare delta and return -> when to do 0.75 delta vs 0.9? When to choose longer date vs shorter? Risk and Liquidity
# Notify when to update futures and quantity: future expiry date, total currency amount (non cad)
# Notify when to roll: delta < 0.6? -> do some analysis
# Create a bunch of virtual portfolios and track them. For each virtual portfolio use different metrics and track which ones perform best 
# Model strategies: stock, stock + itm call, stock + otm call, put
