def yf_currency_symbol(numerator, denominator) -> str:
    if numerator == "USD":
        return denominator + "=X"
    
    return numerator + denominator + "=X"