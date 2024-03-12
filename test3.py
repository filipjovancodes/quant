from ib_insync import IB, Future
from dao import DAO
from local_objects import BorrowBoxStrategyObject, CashStrategyObject, CoveredCallStrategy, CoveredCallStrategyObject, CurrencyHedgeStrategyObject, LongStockStrategyObject, PositionData, PutHedgeStrategyObject

dao = DAO()

# positions = dao.get_positions()

# for position in positions:
#     print(position)

fut = dao.get_futures_price()

positions = dao.get_positions()
for position in positions:
    if position.contract.symbol == "PENN":
        print(position)



# print(fut)