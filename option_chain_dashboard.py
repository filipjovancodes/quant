import dash
from dash import html, dcc, Output, Input, dash_table
import sqlite3
import jsonpickle
from local_objects import OptionData, OptionChainList, StockData


symbol = "WLKP"

# Define your Dash app
app = dash.Dash(__name__)

# Define the layout of your Dash app
app.layout = html.Div(
    [
        html.H1("Option Data Dashboard"),
        dash_table.DataTable(
            id='option-table',
            columns=[
                {'name': 'Symbol', 'id': 'symbol'},
                {'name': 'Stock Price', 'id': 'stockPrice'},
                {'name': 'Bid Size', 'id': 'bidSize'},
                {'name': 'Bid Price', 'id': 'bidPrice'},
                {'name': 'Ask Price', 'id': 'askPrice'},
                {'name': 'Ask Size', 'id': 'askSize'},
                {'name': 'Model Price', 'id': 'optionPrice'},
                {'name': 'Annualized', 'id': 'annualized'},
                {'name': 'Strike', 'id': 'strike'},
                {'name': 'Expiry', 'id': 'expiry'},
                {'name': 'Dividend', 'id': 'dividend'},
                {'name': 'Dividend Periods', 'id': 'dividendPeriods'},
                {'name': 'Delta', 'id': 'delta'},
                {'name': 'Theta', 'id': 'theta'},
                {'name': 'Gamma', 'id': 'gamma'},
                {'name': 'Vega', 'id': 'vega'},
                {'name': 'Call Return', 'id': 'callReturn'},
                {'name': 'Dividend Return', 'id': 'dividendReturn'},
                {'name': 'Total Return', 'id': 'totalReturn'},
                {'name': 'Cost Base', 'id': 'costBase'},
                {'name': 'Days to Expiry', 'id': 'daysToExpiry'},
                {'name': 'Protection', 'id': 'protection'},
                {'name': 'Break Even', 'id': 'breakEven'}
            ],
            style_table={'overflowX': 'scroll'},
            style_cell={'textAlign': 'left', 'minWidth': '180px'},
        ),
        dcc.Interval(
            id="interval-component",
            interval=5*1000,  # in milliseconds
            n_intervals=0
        )
    ]
)

@app.callback(    
    Output("option-table", "data"),
    [Input("interval-component", "n_intervals")]
)
def update_metrics_callback(n):
    # Fetch one row from the database
    conn = sqlite3.connect("test.db")
    cursor = conn.cursor()
    row = cursor.execute("SELECT * FROM OptionChains WHERE symbol = ?", (symbol,)).fetchone()
    conn.close()
    
    # Decode JSON and extract option chain list
    option_chain = jsonpickle.decode(row[1])
    option_chain_data = option_chain.option_chain_list  # Assuming only one option chain in the list
    
    # Format data for the table
    option_data = []
    for option in option_chain_data:
        # print(option)

        option_data.append({
            'symbol': option.symbol,
            'stockPrice': round(option.stockPrice, 2),
            'bidSize': option.bidSize,
            'bidPrice': option.bid,
            'askPrice': option.ask,
            'askSize': option.askSize,
            'optionPrice': round(option.optionPrice, 2),
            'annualized': round(option.annualized() * 100, 2),
            'strike': option.strike,
            'expiry': option.expiry,
            'dividend': option.dividend,
            'dividendPeriods': option.dividendPeriods,
            'delta': round(option.delta * 100, 2),
            'theta': round(option.theta * 100, 2),
            'gamma': round(option.gamma * 100, 2),
            'vega': round(option.vega * 100, 2),
            'callReturn': round(option.callReturn(), 2),
            'dividendReturn': round(option.dividendReturn, 2),
            'totalReturn': round(option.totalReturn(), 2),
            'costBase': round(option.costBase(), 2),
            'daysToExpiry': option.daysToExpiry(),
            'protection': round(option.protection() * 100, 2),
            'breakEven': round(option.breakEven(), 2),
        })
    
    return option_data

# Run the Dash app
if __name__ == "__main__":
    app.run_server(debug=False, port=8051)
