from math import log, sqrt, pi, exp
from scipy.stats import norm
from datetime import datetime, date
import numpy as np
import pandas as pd
from pandas import DataFrame

# TODO put into class

def d1(S,K,T,r,iv):
    return(log(S/K)+(r+iv**2/2)*T)/iv*sqrt(T)
def d2(S,K,T,r,iv):
    return d1(S,K,T,r,iv)-iv*sqrt(T)

def bs_call(S,K,T,r,iv):
    return S*norm.cdf(d1(S,K,T,r,iv))-K*exp(-r*T)*norm.cdf(d2(S,K,T,r,iv))                                                     
def bs_put(S,K,T,r,iv):
    return K*exp(-r*T)-S+bs_call(S,K,T,r,iv)

def call_delta(S,K,T,r,iv):
    return norm.cdf(d1(S,K,T,r,iv))
def call_gamma(S,K,T,r,iv):
    return norm.pdf(d1(S,K,T,r,iv))/(S*iv*sqrt(T))
def call_vega(S,K,T,r,iv):
    return 0.01*(S*norm.pdf(d1(S,K,T,r,iv))*sqrt(T))
def call_theta(S,K,T,r,iv):
    return 0.01*(-(S*norm.pdf(d1(S,K,T,r,iv))*iv)/(2*sqrt(T)) - r*K*exp(-r*T)*norm.cdf(d2(S,K,T,r,iv)))
def call_rho(S,K,T,r,iv):
    return 0.01*(K*T*exp(-r*T)*norm.cdf(d2(S,K,T,r,iv)))

def put_delta(S,K,T,r,iv):
    return -norm.cdf(-d1(S,K,T,r,iv))
def put_gamma(S,K,T,r,iv):
    return norm.pdf(d1(S,K,T,r,iv))/(S*iv*sqrt(T))
def put_vega(S,K,T,r,iv):
    return 0.01*(S*norm.pdf(d1(S,K,T,r,iv))*sqrt(T))
def put_theta(S,K,T,r,iv):
    return 0.01*(-(S*norm.pdf(d1(S,K,T,r,iv))*iv)/(2*sqrt(T)) + r*K*exp(-r*T)*norm.cdf(-d2(S,K,T,r,iv)))
def put_rho(S,K,T,r,iv):
    return 0.01*(-K*T*exp(-r*T)*norm.cdf(-d2(S,K,T,r,iv)))

# r = get_price("^IRX")
# r = r/100; iv = iv/100; -> get iv (iv) from yahoo finance
# price, delta, gamma, vega, rho, theta, 
def get_price_and_greeks(S, K, T, r, iv, right):
    if right == "C":
        return bs_call(S,K,T,r,iv), call_delta(S,K,T,r,iv), call_gamma(S,K,T,r,iv),call_vega(S,K,T,r,iv), call_rho(S,K,T,r,iv), call_theta(S,K,T,r,iv)
    else:
        return bs_put(S,K,T,r,iv), put_delta(S,K,T,r,iv), put_gamma(S,K,T,r,iv),put_vega(S,K,T,r,iv), put_rho(S,K,T,r,iv), put_theta(S,K,T,r,iv)

def implied_volatility(Price,S,K,T,r, right):
    iv = 0.001
    if right == "C":
        while iv < 1:
            Price_implied = S*norm.cdf(d1(S,K,T,r,iv))-K*exp(-r*T)*norm.cdf(d2(S,K,T,r,iv))
            if Price-(Price_implied) < 0.001:
                return iv
            iv += 0.001
        return None
    else:
        while iv < 1:
            Price_implied = K*exp(-r*T)-S+bs_call(S,K,T,r,iv)
            if Price-(Price_implied) < 0.001:
                return iv
            iv += 0.001
        return None
    