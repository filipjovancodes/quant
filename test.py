

from portfolio_dashboard import OptionChainDashboard


option_chain_dashboard = OptionChainDashboard()
option_chain_dashboard.run_server()

# async def place_order(ib: IB, symbol):
#     contract = Stock(symbol, "SMART", "USD")  # Define contract details
#     # order = ...     # Define order details
#     # orderId = await ib.placeOrderAsync(contract, order)
#     data = await ib.reqTickersAsync(contract)  # Await the result of the async operation
#     print(f"Data: {data}")

# async def run():
#     ib = IB()
#     util.startLoop()
#     await ib.connectAsync('127.0.0.1', 7496, clientId=1, readonly=True)  # Connect to IBKR TWS or IB Gateway

#     # Execute async functions concurrently
#     await asyncio.gather(
#         place_order(ib, "AAPL"),  # Pass the coroutine object directly
#         place_order(ib, "MSFT"),  # Pass the coroutine object directly
#     )

#     ib.disconnect()

# if __name__ == "__main__":
#     util.run(run())

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
