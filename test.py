from datetime import datetime
import math
import pandas as pd
from yahoo_fin import stock_info as si
from yahoo_fin import options as op
import yfinance as yf
from dateutil.relativedelta import relativedelta

import csv

from src.asset import Asset

symbol = "AAPL"




a = Asset(symbol)

div = a.get_dividend_yield_simple()


# calls = op.get_options_chain(symbol, "20240419")["calls"]
# strikes = calls["Strike"].values
# nd_per_share = 123.44

# print(strikes)

# target_strike = math.floor(nd_per_share)
# max_itr_strike = 100
# j = 0
# while j < max_itr_strike:
#     strike_check = [target_strike - 0.5 * j, target_strike + 0.5 * j]
#     for strike in strike_check:
#         if strike in strikes:
#             target_strike = strike
#             j = max_itr_strike
#             break
#     j += 1

# print(target_strike)


def format_date(year: int, month: int, day: int) -> str:
    output = str(year)
    m = str(month)
    if len(m) == 1:
        m = "0" + m
    output += m
    d = str(day)
    if len(d) == 1:
        d = "0" + d
    output += d

    return output

nd_per_share = 123.34

d = datetime.now()
target_expiry = d + relativedelta(months = 6)
target_strike = math.floor(nd_per_share)

max_itr_days = 100
i = 0
option = None
while i < max_itr_days:
    date_prev = target_expiry + relativedelta(days = i)
    date_prev = format_date(year = date_prev.year, month = date_prev.month, day = date_prev.day)
    date_next = target_expiry - relativedelta(days = i)
    date_next = format_date(year = date_next.year, month = date_next.month, day = date_next.day)
    expiries = [date_prev, date_next]
    
    for expiry in expiries:
        try:
            calls = op.get_options_chain(symbol, expiry)["calls"]
            strikes = calls["Strike"].values

            max_itr_strike = 100
            j = 0
            while j < max_itr_strike:
                strike_check = [target_strike - 0.5 * j, target_strike + 0.5 * j]
                for strike in strike_check:
                    if strike in strikes:
                        target_strike = strike
                        j = max_itr_strike
                        break
                j += 1

            print(target_expiry, target_strike)

            target_expiry = expiry
            i = max_itr_days
            break

        except:
            pass

    i += 1

print(target_expiry, target_strike)

