from datetime import datetime
import sqlite3
import time
from ib_insync import IB, Option, Stock
import jsonpickle
import pytz
import scipy.optimize as optimize
import yfinance
from local_objects import OptionChainList, OptionPosition


symbol = "CCRN"

class OptionChain:
    def __init__(self, ib, symbol):
        self.ib = ib
        self.symbol = symbol
        self.initialize()

    def initialize(self):
        self.stockContract = Stock(self.symbol, "SMART", "USD")
        self.ib.qualifyContracts(self.stockContract)
        self.stockTicker = self.ib.reqTickers(self.stockContract)[0]
        chains = self.ib.reqSecDefOptParams(
            self.stockContract.symbol,
            "",
            self.stockContract.secType,
            self.stockContract.conId,
        )
        self.option_chain = [x for x in chains if x.exchange == "SMART"][0]
        # self.expiries = self.find_closest_expiry(self.option_chain.expirations, [1, 2, 3, 6, 12])
        self.expiries = self.option_chain.expirations[1:]
        # self.strikes = self.filter_closest_strikes(self.option_chain.strikes, self.stockTicker.marketPrice(), 5) 
        self.strikes = self.option_chain.strikes

        prospectContracts = []
        for expiry in self.expiries:
            for strike in self.strikes:
                prospectContracts.append(Option(self.stockContract.symbol, expiry, strike, 'C', 'SMART', '100', 'USD'))
        self.ib.qualifyContracts(*prospectContracts)

        prospectTickers = self.ib.reqTickers(*prospectContracts)
        self.ib.sleep(1)

        self.optionContracts = [x.contract for x in prospectTickers if x.modelGreeks is not None]

        i = 0
        while True:
            print(f"Updating {i}")
            self.update_tickers()
            print(f"Update complete")
            self.ib.sleep(10)
            i += 1

    def update_tickers(self):
        self.stockTicker = self.ib.reqTickers(self.stockContract)[0]
        self.optionTickers = self.ib.reqTickers(*self.optionContracts)
        self.ib.sleep(1)

        conn = sqlite3.connect("test.db")
        cursor = conn.cursor()

        cursor.execute(
            """CREATE TABLE IF NOT EXISTS OptionChains (
                symbol TEXT PRIMARY KEY,
                optionChain TEXT
            )"""
        )

        optionChain = OptionChainList()
        for ticker in self.optionTickers:
            optionChain.option_chain_list.append(OptionPosition(ticker))

        sql = """INSERT OR REPLACE INTO OptionChains (symbol, optionChain) VALUES (?, ?)"""
        cursor.execute(sql, [self.symbol, jsonpickle.encode(optionChain)])

        conn.commit()
        conn.close()

    def filter_closest_strikes(self, strikes, target, number_strikes):
        if len(strikes) <= number_strikes:
            return strikes

        # Calculate the absolute difference between each number and the target
        differences = [(abs(strike - target), strike) for strike in strikes]

        # Sort the differences in ascending order
        differences.sort()

        # Select the 10 numbers with the smallest differences
        closest_strikes = [strike for diff, strike in differences[:number_strikes]]

        closest_strikes.sort()

        return closest_strikes

    def find_closest_expiry(self, expiries, months):
        # Convert expiry dates to datetime objects
        expiry_dates = [datetime.strptime(expiry, "%Y%m%d") for expiry in expiries]

        # Get today's date
        today = datetime.now()

        # Calculate the difference between each expiry date and today's date
        time_diffs = [(expiry - today).days for expiry in expiry_dates]

        # Convert months to days
        months_to_days = {3: 90, 6: 180, 12: 365, 24: 730}

        # Find the expiry dates closest to the specified number of months away from today
        closest_expiries = []
        for month in months:
            days = months_to_days[month]
            closest_index = min(
                range(len(time_diffs)), key=lambda i: abs(time_diffs[i] - days)
            )
            closest_expiries.append(expiry_dates[closest_index])

        # Filter out any duplicate dates
        closest_expiries = list(set(closest_expiries))

        # Convert the closest expiry dates back to string format
        closest_expiry_strings = [
            expiry.strftime("%Y%m%d") for expiry in closest_expiries
        ]

        closest_expiry_strings.sort()

        return closest_expiry_strings

    # def optionDataToDashboard(self, option_data):
    #     return [
    #         option_data.symbol,
    #         option_data.stockPrice,
    #         option_data.optionPrice,
    #         option_data.strike,
    #         option_data.expiry,
    #         option_data.dividend,
    #         option_data.dividendPeriods,
    #         option_data.delta,
    #         option_data.theta,
    #         option_data.gamma,
    #         option_data.vega,
    #         option_data.callReturn(),
    #         option_data.dividendReturn(),
    #         option_data.totalReturn(),
    #         option_data.costBase(),
    #         option_data.daysToExpiry(),
    #         option_data.annualized(),
    #         option_data.protection(),
    #         option_data.breakEven(),
    #     ]


def start():
    ib = IB()
    ib.connect("127.0.0.1", 7496, clientId=1, readonly=True)
    for i in range(1, 5):
        ib.reqMarketDataType(i)

    OptionChain(ib, symbol)


start()

# exit()
    

def test():

    # Given inputs
    days = 39
    call = 1.9
    stock = 23.87
    strike = 22.5
    dividend = 0.2
    periods = 1
    rfr = 0.047
    required_return = rfr + 0.02


    def calculate_annualized(put_price):
        call_return = call + strike - stock
        dividend_return = dividend * periods
        call_return = call_return + dividend_return
        net_return = call_return - put_price
        cost_base = stock - call + put_price
        annualized = (1 + net_return / cost_base) ** (365 / days) - 1
        return -annualized  # Minimize negative annualized return


    # Initial guess for put price
    put_guess = 1.0

    # Bounds for put price (typically non-negative)
    bounds = optimize.Bounds(0, float("inf"))


    # Constraint function
    def constraint_function(put_price):
        return calculate_annualized(put_price) + required_return


    # Constraint definition
    constraints = {"type": "ineq", "fun": constraint_function}

    # Optimization
    result = optimize.minimize(
        calculate_annualized, put_guess, bounds=bounds, constraints=constraints
    )

    # Extract optimized put price
    optimal_put_price = result.x[0]

    # Calculate corresponding annualized return
    optimal_annualized_return = -result.fun

    print("Optimal Put Price:", optimal_put_price)
    print("Corresponding Annualized Return:", optimal_annualized_return)
