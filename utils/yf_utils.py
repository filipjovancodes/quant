def yf_currency_symbol(numerator, denominator) -> str:
    if numerator == "USD":
        return denominator + "=X"
    
    return numerator + denominator + "=X"

def yf_symbol(self) -> str:
        symbol = self.position.contract.symbol
        exchange = self.position.contract.exchange

        s = symbol.replace(".", "-")
        if exchange == "TSE":
            s += ".TO"
        elif exchange == "VENTURE":
            s += ".V"
        elif exchange == "LSE":
            s += ".L"
        elif symbol == "MCD" or symbol == "M6B":
            s += "=F"
        return s