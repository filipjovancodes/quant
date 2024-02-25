class Option:
    # TODO build own model with rate and rho data
    # ticker = ticker of option
    # right = type of option (call, put)
    # stock_price = stock price
    # strike = option strike
    # expiry = days to option expiry -> TODO make actual option date instead
    # rate = continuous interest rate
    # iv = implied volatility
    # option_price = option price
    def __init__(
            self,
            ticker = None,
            right = None,
            stock_price = None,
            strike = None,
            expiry = None,
            rate = None,
            iv = None,
            option_price = None,
            delta = None,
            gamma = None,
            vega = None,
            rho = None,
            theta = None
        ):
        self.ticker = ticker
        self.right = right
        self.stock_price = stock_price
        self.strike = strike
        self.expiry = expiry
        self.rate = rate
        self.iv = iv
        self.option_price = option_price
        self.delta = delta
        self.gamma = gamma
        self.vega = vega
        self.rho = rho
        self.theta = theta

    def to_list(self):
        return [
            self.ticker,
            self.right,
            self.stock_price,
            self.strike,
            self.expiry,
            self.rate,
            self.iv,
            self.option_price,
            self.delta,
            self.gamma,
            self.vega,
            self.rho,
            self.theta
        ]
    
    def __str__(self):
        to_return = f"ticker: {self.ticker}\n"
        to_return += f"right: {self.right}\n"
        to_return += f"stock_price: {self.stock_price}\n"
        to_return += f"strike: {self.strike}\n"
        to_return += f"expiry: {self.expiry}\n"
        to_return += f"rate: {self.rate}\n"
        to_return += f"iv: {self.iv}\n"
        to_return += f"option_price: {self.option_price}\n"
        to_return += f"delta: {self.delta}\n"
        to_return += f"gamma: {self.gamma}\n"
        to_return += f"vega: {self.vega}\n"
        to_return += f"rho: {self.rho}\n"
        to_return += f"theta: {self.theta}\n"
        return to_return