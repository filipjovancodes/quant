from dao import DAO
from portfolio_dashboard import PortfolioDashboard


def update_data(dao):
    dao.update_rfr_data()
    dao.commit()

    dao.update_currency_data()
    dao.commit()

    dao.update_position_data()
    dao.commit()

    dao.update_futures_data()
    dao.commit()

    dao.update_stock_data()
    dao.commit()

    dao.update_option_data()
    dao.commit()

    dao.update_strategy_data_new()
    dao.commit()

    pass



dao = DAO()
update_data(dao)
pd = PortfolioDashboard(dao)
pd.display_dashboard()


# "BBY", "SMART", "USD", "100", "20250117", 35, 25.3, 1, 0.1, 5 # 74.15
# t2 = threading.Thread(target=ui.start_trade_covered_call, args=("HCC", "SMART", "USD", "100", "20240419", 35, 27, 1, 0.1, 5)) # 61.25
# t2.start()

# tm = TradeManager(dao)
# tm.start_trade_put()


dao.close()