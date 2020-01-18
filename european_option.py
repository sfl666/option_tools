"""
Author: shifulin
Email: shifulin666@qq.com
"""
from math import log, sqrt, exp
import numpy as np
from scipy.stats import norm


# def bs_call(s, k, sigma, r, t):
#     d1 = (np.log(s / k) + (r + pow(sigma, 2) / 2.0) * t) / (sigma * np.sqrt(t))
#     d2 = d1 - sigma * np.sqrt(t)
#     return s * norm.cdf(d1) - k * np.exp(-r * t) * norm.cdf(d2)
#
#
# def bs_put(s, k, sigma, r, t):
#     d1 = (np.log(s / k) + (r + pow(sigma, 2) / 2.0) * t) / (sigma * np.sqrt(t))
#     d2 = d1 - sigma * np.sqrt(t)
#     return k * np.exp(-r * t) * norm.cdf(-d2) - s * norm.cdf(-d1)


def delta(s, k, sigma, r, t, option_type):
    d1 = (np.log(s / k) + (r + pow(sigma, 2) / 2.0) * t) / (sigma * np.sqrt(t))
    if option_type == 'Call':
        return norm.cdf(d1)
    else:
        return norm.cdf(d1) - 1.0


def gamma(s, k, sigma, r, t):
    d1 = (np.log(s / k) + (r + pow(sigma, 2) / 2.0) * t) / (sigma * np.sqrt(t))
    return np.exp(-pow(d1, 2) / 2.0) / (s * sigma * np.sqrt(2.0 * np.pi * t))


def theta(s, k, sigma, r, t, option_type):
    d1 = (np.log(s / k) + (r + pow(sigma, 2) / 2.0) * t) / (sigma * np.sqrt(t))
    d2 = d1 - sigma * np.sqrt(t)
    theta_call = -(s * sigma * np.exp(-pow(d1, 2) / 2.0)) / (2.0 * np.sqrt(2.0 * np.pi * t)) - \
        r * k * np.exp(-r * t) * norm.cdf(d2)
    if option_type == 'Call':
        return theta_call
    else:
        return theta_call + r * k * np.exp(-r * t)


def vega(s, k, sigma, r, t):
    d1 = (np.log(s / k) + (r + pow(sigma, 2) / 2.0) * t) / (sigma * np.sqrt(t))
    return s * np.sqrt(t) * np.exp(-pow(d1, 2) / 2.0) / np.sqrt(2.0 * np.pi)


def rho(s, k, sigma, r, t, option_type):
    d1 = (np.log(s / k) + (r + pow(sigma, 2) / 2.0) * t) / (sigma * np.sqrt(t))
    d2 = d1 - sigma * np.sqrt(t)
    if option_type == 'Call':
        return k * t * np.exp(-r * t) * norm.cdf(d2)
    else:
        return -k * t * np.exp(-r * t) * norm.cdf(-d2)


def bs_call(s, k, sigma, r, t):
    tmp = sqrt(t)
    d1 = (log(s / k) + (r + pow(sigma, 2) / 2.0) * t) / (sigma * tmp)
    d2 = d1 - sigma * tmp
    return s * norm.cdf(d1) - k * exp(-r * t) * norm.cdf(d2)


def bs_put(s, k, sigma, r, t):
    tmp = sqrt(t)
    d1 = (log(s / k) + (r + pow(sigma, 2) / 2.0) * t) / (sigma * tmp)
    d2 = d1 - sigma * tmp
    return k * exp(-r * t) * norm.cdf(-d2) - s * norm.cdf(-d1)


def call_iv(c, s, k, t, r=0.03, sigma_min=0.01, sigma_max=1.0, e=0.00001):
    sigma_mid = (sigma_min + sigma_max) / 2.0
    call_min = bs_call(s, k, sigma_min, r, t)
    call_max = bs_call(s, k, sigma_max, r, t)
    call_mid = bs_call(s, k, sigma_mid, r, t)
    diff = c - call_mid
    if c <= call_min:
        return sigma_min
    elif c >= call_max:
        return sigma_max
    while abs(diff) > e:
        if c > call_mid:
            sigma_min = sigma_mid
        else:
            sigma_max = sigma_mid
        sigma_mid = (sigma_min + sigma_max) / 2.0
        call_mid = bs_call(s, k, sigma_mid, r, t)
        diff = c - call_mid
    # print(sigma_mid)
    return sigma_mid


def put_iv(c, s, k, t, r=0.03, sigma_min=0.01, sigma_max=1.0, e=0.00001):
    sigma_mid = (sigma_min + sigma_max) / 2.0
    put_min = bs_put(s, k, sigma_min, r, t)
    put_max = bs_put(s, k, sigma_max, r, t)
    put_mid = bs_put(s, k, sigma_mid, r, t)
    diff = c - put_mid
    if c <= put_min:
        return sigma_min
    elif c >= put_max:
        return sigma_max
    while abs(diff) > e:
        if c > put_mid:
            sigma_min = sigma_mid
        else:
            sigma_max = sigma_mid
        sigma_mid = (sigma_min + sigma_max) / 2.0
        put_mid = bs_put(s, k, sigma_mid, r, t)
        diff = c - put_mid
    return sigma_mid


def my_test():
    call_iv(0.138, 3.046, 3.1, 0.5, r=0.03, sigma_min=0.01, sigma_max=1.0, e=0.000001)


def my_test2():
    import matplotlib.pyplot as plt
    a = np.linspace(0, 0.8, 100)
    yc, yp = [], []
    for i in a:
        yc.append(vega(6.0, 5.0, i, 0.03, 0.5))
        yp.append(vega(6.0, 5.0, i, 0.03, 0.5))
    plt.plot(yc)
    plt.plot(yp)
    plt.show()


if __name__ == '__main__':
    my_test2()

