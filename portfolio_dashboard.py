import asyncio
from collections import Counter
from ib_insync import IB, Option, Stock, util
import pandas as pd
from local_objects import (
    BorrowBoxStrategy,
    BorrowBoxStrategyObject,
    CashStrategy,
    CashStrategyObject,
    CoveredCallPutStrategy,
    CoveredCallPutStrategyObject,
    CoveredCallStrategy,
    CoveredCallStrategyObject,
    CurrencyHedgeStrategy,
    CurrencyHedgeStrategyObject,
    LongStockStrategy,
    LongStockStrategyObject,
    PutHedgeStrategy,
    PutHedgeStrategyObject,
)
import dash
from dash import dcc, html
import plotly.express as px
from dash.dependencies import Input, Output
from datetime import datetime, timedelta


class PortfolioDashboard:
    def __init__(self, dao):
        self.dao = dao
        self.portfolio_strategy_list = []
        self.total = 0
        self.annual_return = 0
        self.beta = 0
        self.delta = 0
        self.theta = 0
        self.gamma = 0
        self.vega = 0
        self.industries_list = []
        self.sectors_list = []
        self.strategy_values = []
        self.risk_values = []
        self.return_values = []
        self.covered_call_symbols = []
        self.valuation_values = []

        self.initialize()

    def initialize(self):
        print("Building strategies")

        strategy_list = self.dao.get_strategies()

        for strategy_object in strategy_list:
            if isinstance(strategy_object, CoveredCallStrategyObject):
                strategy = CoveredCallStrategy(
                    self.dao,
                    strategy_object.stock_position,
                    strategy_object.option_position,
                )
            elif isinstance(strategy_object, PutHedgeStrategyObject):
                strategy = PutHedgeStrategy(self.dao, strategy_object.option_position)
            elif isinstance(strategy_object, LongStockStrategyObject):
                strategy = LongStockStrategy(self.dao, strategy_object.stock_position)
            elif isinstance(strategy_object, CurrencyHedgeStrategyObject):
                strategy = CurrencyHedgeStrategy(
                    self.dao, strategy_object.future_position
                )
            elif isinstance(strategy_object, CashStrategyObject):
                strategy = CashStrategy(self.dao, strategy_object.cash_balance)
            elif isinstance(strategy_object, BorrowBoxStrategyObject):
                strategy = BorrowBoxStrategy(
                    self.dao,
                    strategy_object.long_put,
                    strategy_object.short_call,
                    strategy_object.short_put,
                    strategy_object.long_call
                )
            elif isinstance(strategy_object, CoveredCallPutStrategyObject):
                strategy = CoveredCallPutStrategy(
                    self.dao,
                    strategy_object.stock_position,
                    strategy_object.call_position,
                    strategy_object.put_position
                )

            self.portfolio_strategy_list.append(strategy)

        for strategy in self.portfolio_strategy_list:
            portfolio_strategy = PortfolioStrategy(strategy)
            self.strategy_values.append(portfolio_strategy)
            self.industries_list.append(portfolio_strategy.industry)
            self.sectors_list.append(portfolio_strategy.sector)

            if isinstance(strategy, CoveredCallStrategy):
                self.risk_values.append(
                    strategy.beta() * strategy.delta()
                )  # Calculate risk
                self.return_values.append(strategy.annualized())  # Annualized return
                self.covered_call_symbols.append(strategy.symbol())
                self.valuation_values.append(strategy.valuation_values())

            # Update portfolio values
            self.total += portfolio_strategy.totalCAD  # Total CAD
            self.annual_return += portfolio_strategy.returnCAD  # Return CAD

        for strategy in self.portfolio_strategy_list:
            self.add_strategy_to_portfolio(strategy)

        for i in range(0, len(self.strategy_values)):
            self.strategy_values[i].percentPortfolio = round(
                self.strategy_values[i].totalCAD / self.total * 100, 2
            )

    def display_dashboard(self):
        app = dash.Dash()

        # Define layout
        app.layout = html.Div(
            children=[
                self.portfolio_summary_table(),
                self.covered_call_table(),
                self.valuation_table(),
                self.risk_return_plot(),
                self.industry_chart(),
                self.sector_chart(),
            ]
        )

        app.run_server(debug=False, port=8050)

    def add_strategy_to_portfolio(self, strategy):
        self.beta += (strategy.beta() * strategy.stock_exposure()) / self.total  # Beta
        self.delta += (
            strategy.delta() * strategy.stock_exposure()
        ) / self.total  # Delta
        self.theta += strategy.theta() * strategy.quantity() / 100  # Theta
        self.gamma += (
            strategy.gamma() * strategy.stock_exposure()
        ) / self.total  # Gamma
        self.vega += (strategy.vega() * strategy.option_exposure()) / self.total  # Vega

    def portfolio_summary_table(self):
        return dcc.Graph(
            id="portfolio-table",
            figure={
                "data": [
                    {
                        "type": "table",
                        "header": dict(
                            values=[
                                "Total Portfolio Value",
                                "Return",
                                "Annualized % (Return/Portfolio Value)",
                                "Beta",
                                "Delta",
                                "Theta",
                                "Gamma",
                                "Vega",
                            ],
                        ),
                        "cells": dict(
                            values=[
                                round(self.total, 0),
                                round(self.annual_return, 0),
                                round(
                                    self.annual_return / self.total * 100, 2
                                ),  # Annualized return percentage
                                round(self.beta, 2),
                                round(self.delta, 4),
                                round(self.theta * 100, 2),
                                round(self.gamma * 100, 2),
                                round(self.vega * 100, 2),
                            ]
                        ),
                    }
                ]
            },
        )

    def covered_call_table(self):
        sorted_values = sorted(self.strategy_values, key=lambda x: x.symbol)
        result = [x.to_list() for x in sorted_values]

        # Create DataFrame for strategy values
        df = pd.DataFrame(
            result,
            columns=[
                "Symbol",
                "Net Price",
                "Quantity",
                "Annualized",
                "Total CAD",
                "PercentPortfolio",
                "Return CAD",
                "Industry",
                "Sector",
                "Beta",
                "Delta",
                "Theta",
                "Gamma",
                "Vega",
                "Expiry",
            ],
        )

        fig_cc_table = {
            "data": [
                {
                    "type": "table",
                    "header": dict(values=df.columns),
                    "cells": dict(values=df.values.T),
                }
            ]
        }

        return dcc.Graph(id="covered-call-table", figure=fig_cc_table)

    def valuation_table(self):
        val_df = pd.DataFrame(
            self.valuation_values,
            columns=[
                "Symbol",
                "Stock Price",
                "Shares Issued (M)",
                "Market Cap (M)",
                # "Net Debt (M)",
                "Total Equity (M)",
                "Cashflow Average (M)",
                "P/E",
                "EPS",
                "DCF Stock Price",
                "Liquid Stock Price",
            ],
        )

        fig_valuation_table = {
            "data": [
                {
                    "type": "table",
                    "header": dict(values=val_df.columns),
                    "cells": dict(values=val_df.values.T),
                }
            ]
        }

        return dcc.Graph(id="valuation-table", figure=fig_valuation_table)

    def risk_return_plot(self):
        fig = px.scatter(
            x=self.risk_values,
            y=self.return_values,
            text=self.covered_call_symbols,
            labels={"x": "Risk", "y": "Return"},
            title="Risk/Return Plot",
        )

        return dcc.Graph(id="risk-return-plot", figure=fig)

    def industry_chart(self):
        industries = Counter(self.industries_list)
        fig_industry = px.pie(
            values=list(industries.values()),
            names=list(industries.keys()),
            title="Industry Distribution",
        )

        return dcc.Graph(id="industry-pie-chart", figure=fig_industry)

    def sector_chart(self):
        sectors = Counter(self.sectors_list)
        fig_sector = px.pie(
            values=list(sectors.values()),
            names=list(sectors.keys()),
            title="Sector Distribution",
        )

        return dcc.Graph(id="sector-pie-chart", figure=fig_sector)


class PortfolioStrategy:
    def __init__(self, strategy):
        self.symbol = strategy.symbol()
        self.netPrice = round(strategy.netPrice(), 2)
        self.quantity = round(strategy.quantity(), 2)
        self.annualized = round(strategy.annualized() * 100, 2)
        self.totalCAD = round(strategy.totalCAD(), 2)
        self.percentPortfolio = 0
        self.returnCAD = round(strategy.returnCAD(), 2)
        self.industry = strategy.industry()
        self.sector = strategy.sector()
        self.beta = round(strategy.beta(), 2)
        self.delta = round(strategy.delta(), 4)
        self.theta = round(strategy.theta() * 100, 2)
        self.gamma = round(strategy.gamma() * 100, 2)
        self.vega = round(strategy.vega() * 100, 2)
        self.expiry = strategy.expiry()

    def to_list(self):
        return [
            self.symbol,
            self.netPrice,
            self.quantity,
            self.annualized,
            self.totalCAD,
            self.percentPortfolio,
            self.returnCAD,
            self.industry,
            self.sector,
            self.beta,
            self.delta,
            self.theta,
            self.gamma,
            self.vega,
            self.expiry,
        ]

    def __repr__(self):
        return (
            f"PortfolioDashboard(symbol={self.symbol}, netPrice={self.netPrice}, "
            f"quantity={self.quantity}, annualized={self.annualized}, totalCAD={self.totalCAD}, "
            f"returnCAD={self.returnCAD}, industry={self.industry}, sector={self.sector}, "
            f"beta={self.beta}, delta={self.delta}, theta={self.theta}, gamma={self.gamma}, "
            f"vega={self.vega}), expiry={self.expiry}"
        )


class OptionChainDashboard:
    def __init__(self):
        self.app = dash.Dash(__name__)
        self.ib = IB()
        util.startLoop()
        self.ib.connect('127.0.0.1', 7496, clientId=1, readonly=True)  # Connect to TWS or IB Gateway
        self.ib.reqMarketDataType(1)

        # Define layout
        self.app.layout = html.Div(children=[
            html.H1(children='Live Option Chain Dashboard'),
            dcc.Interval(
                id='interval-component',
                interval=10 * 1000,  # in milliseconds
                n_intervals=0
            ),
            html.Div(id='option-chain-container')
        ])

        # Define callback to update option chain
        @self.app.callback(
            Output('option-chain-container', 'children'),
            [Input('interval-component', 'n_intervals')]
        )
        def update_option_chain(n):
            self.update_option_chain_async()

    async def update_option_chain_async(self):
        # Retrieve option chain data
        stock_symbol = 'AAPL'  # You can change this to the desired stock symbol
        stock = Stock(stock_symbol, 'SMART', 'USD')
        self.ib.qualifyContracts(stock)
        tickers = self.ib.reqTickers(stock)
        stock_price = tickers[0].marketPrice()
        option_chain = self.ib.reqSecDefOptParams(stock.symbol, "", stock.secType, stock.conId)[0]

        # Find 1 month out option chain
        expiries = self.find_closest_expiry(option_chain.expirations, [3, 6, 12, 24])

        strikes = self.filter_closest_strikes(option_chain.strikes, stock_price, 5)

        expiries = [expiries[0]]

        option_contracts = []
        for expiry in expiries:
            for strike in strikes:
                option_contracts.append(Option(stock.symbol, expiry, strike, 'C', 'SMART', '100', 'USD'))
        self.ib.qualifyContracts(*option_contracts)

        option_chain_data = []
        for option_contract in option_contracts:
            self.ib.reqMktData(option_contract, '', False, False)
            ticker = self.ib.ticker(option_contract)
            await asyncio.sleep(0.1)  # Sleep to allow time for data to be retrieved
            if ticker.marketPrice() > 0:  # Only include options with valid market price
                option_chain_data.append({
                    'symbol': option_contract.symbol,
                    'strike': option_contract.strike,
                    'last': ticker.marketPrice(),
                    'bid': ticker.bid,
                    'ask': ticker.ask,
                    'expiry': option_contract.lastTradeDateOrContractMonth
                })

        # Create table to display option chain data
        table_rows = [
            html.Tr([
                html.Td(option['symbol']),
                html.Td(option['strike']),
                html.Td(option['last']),
                html.Td(option['bid']),
                html.Td(option['ask']),
                html.Td(option['expiry'])
            ]) for option in option_chain_data
        ]

        option_table = html.Table([
            html.Thead([
                html.Tr([
                    html.Th('Symbol'),
                    html.Th('Strike'),
                    html.Th('Last'),
                    html.Th('Bid'),
                    html.Th('Ask'),
                    html.Th('Expiry')
                ])
            ]),
            html.Tbody(table_rows)
        ])

        return option_table

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
        expiry_dates = [datetime.strptime(expiry, '%Y%m%d') for expiry in expiries]

        # Get today's date
        today = datetime.now()

        # Calculate the difference between each expiry date and today's date
        time_diffs = [(expiry - today).days for expiry in expiry_dates]

        # Convert months to days
        months_to_days = {
            3: 90,
            6: 180,
            12: 365,
            24: 730
        }

        # Find the expiry dates closest to the specified number of months away from today
        closest_expiries = []
        for month in months:
            days = months_to_days[month]
            closest_index = min(range(len(time_diffs)), key=lambda i: abs(time_diffs[i] - days))
            closest_expiries.append(expiry_dates[closest_index])

        # Filter out any duplicate dates
        closest_expiries = list(set(closest_expiries))

        # Convert the closest expiry dates back to string format
        closest_expiry_strings = [expiry.strftime('%Y%m%d') for expiry in closest_expiries]

        closest_expiry_strings.sort()

        return closest_expiry_strings

    def run_server(self):
        self.app.run_server(debug=False, port=8050)