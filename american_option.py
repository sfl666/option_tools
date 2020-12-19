"""
Author: shifulin
Email: shifulin666@qq.com
"""
from math import sqrt, exp, inf
import numpy as np


def _call_price(s, k, sigma, r, t, steps=100):
    r_ = exp(r * (t / steps))
    r_reciprocal = 1.0 / r_
    u = exp(sigma * sqrt(t / steps))
    d = 1.0 / u
    u_square = u ** 2
    p_u = (r_ - d) / (u - d)
    p_d = 1.0 - p_u
    prices = np.zeros(steps + 1)
    prices[0] = s * d ** steps
    for i in range(1, steps + 1):
        prices[i] = prices[i - 1] * u_square
    values = np.zeros(steps + 1)
    for i in range(steps + 1):
        values[i] = max(0.0, prices[i] - k)
    for j in range(steps, 0, -1):
        for i in range(j):
            values[i] = (p_u * values[i + 1] + p_d * values[i]) * r_reciprocal
            prices[i] = d * prices[i + 1]
            values[i] = max(values[i], prices[i] - k)
    # print(values)
    return values[0]


def _put_price(s, k, sigma, r, t, steps=100):
    r_ = exp(r * (t / steps))
    r_reciprocal = 1.0 / r_
    u = exp(sigma * sqrt(t / steps))
    d = 1.0 / u
    u_square = u ** 2
    p_u = (r_ - d) / (u - d)
    p_d = 1.0 - p_u
    prices = np.zeros(steps + 1)
    prices[0] = s * d ** steps
    for i in range(1, steps + 1):
        prices[i] = prices[i - 1] * u_square
    values = np.zeros(steps + 1)
    for i in range(steps + 1):
        values[i] = max(0, k - prices[i])
    for j in range(steps, 0, -1):
        for i in range(0, j):
            values[i] = (p_u * values[i + 1] + p_d * values[i]) * r_reciprocal
            prices[i] = d * prices[i + 1]
            values[i] = max(values[i], k - prices[i])
    return values[0]


def call_price(s, k, sigma, r, t, steps=100):
    return (_call_price(s, k, sigma, r, t, steps) + _call_price(s, k, sigma, r, t, steps + 1)) / 2.0


def put_price(s, k, sigma, r, t, steps=100):
    return (_put_price(s, k, sigma, r, t, steps) + _put_price(s, k, sigma, r, t, steps + 1)) / 2.0


def delta(s, k, sigma, r, t, option_type, steps=100):
    if t == 0.0:
        if s == k:
            return {'Call': 0.5, 'Put': -0.5}[option_type]
        elif s > k:
            return {'Call': 1.0, 'Put': 0.0}[option_type]
        else:
            return {'Call': 0.0, 'Put': -1.0}[option_type]
    else:
        price_func = {'Call': call_price, 'Put': put_price}[option_type]
        return (price_func(s + 0.01, k, sigma, r, t, steps=steps) -
                price_func(s - 0.01, k, sigma, r, t, steps=steps)) * 50.0


def gamma(s, k, sigma, r, t, option_type, steps=100):
    if t == 0.0:
        return inf if s == k else 0.0
    price_func = {'Call': call_price, 'Put': put_price}[option_type]
    return (price_func(s + 0.01, k, sigma, r, t, steps=steps) +
            price_func(s - 0.01, k, sigma, r, t, steps=steps) -
            price_func(s, k, sigma, r, t, steps=steps) * 2.0) * 10000.0


def theta(s, k, sigma, r, t, option_type, steps=100):
    price_func = {'Call': call_price, 'Put': put_price}[option_type]
    t_unit = 1.0 / 365.0
    if t <= t_unit:
        return price_func(s, k, sigma, r, 0.0001, steps=steps) - \
               price_func(s, k, sigma, r, t, steps=steps)
    else:
        return price_func(s, k, sigma, r, t - t_unit, steps=steps) - \
               price_func(s, k, sigma, r, t, steps=steps)


def vega(s, k, sigma, r, t, option_type, steps=100):
    price_func = {'Call': call_price, 'Put': put_price}[option_type]
    if sigma < 0.02:
        return 0.0
    else:
        return (price_func(s, k, sigma + 0.01, r, t, steps=steps) -
                price_func(s, k, sigma - 0.01, r, t, steps=steps)) * 50.0


def rho(s, k, sigma, r, t, option_type, steps=100):
    price_func = {'Call': call_price, 'Put': put_price}[option_type]
    return (price_func(s, k, sigma, r + 0.001, t, steps=steps) -
            price_func(s, k, sigma, r - 0.001, t, steps=steps)) * 500.0


def call_iv(c, s, k, t, r=0.03, sigma_min=0.01, sigma_max=3.0, e=0.00001, steps=100):
    sigma_mid = (sigma_min + sigma_max) / 2.0
    call_min = call_price(s, k, sigma_min, r, t, steps)
    call_max = call_price(s, k, sigma_max, r, t, steps)
    call_mid = call_price(s, k, sigma_mid, r, t, steps)
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
        call_mid = call_price(s, k, sigma_mid, r, t, steps)
        diff = c - call_mid
    # print(sigma_mid)
    return sigma_mid


def put_iv(c, s, k, t, r=0.03, sigma_min=0.01, sigma_max=3.0, e=0.00001, steps=100):
    sigma_mid = (sigma_min + sigma_max) / 2.0
    put_min = put_price(s, k, sigma_min, r, t, steps)
    put_max = put_price(s, k, sigma_max, r, t, steps)
    put_mid = put_price(s, k, sigma_mid, r, t, steps)
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
        put_mid = put_price(s, k, sigma_mid, r, t, steps)
        diff = c - put_mid
    return sigma_mid


def my_test():
    import matplotlib.pyplot as plt
    a = np.linspace(1.0 / 365.0, 2, 100)
    yc, yp = [], []
    for i in a:
        yc.append(vega(6.0, 5.0, 0.25, 0.03, i, option_type='Call', steps=100))
        yp.append(vega(6.0, 5.0, 0.25, 0.03, i, option_type='Put', steps=100))
    plt.plot(yc)
    plt.plot(yp)
    plt.show()


def my_test2():
    # print(call_price(5.0, 5.0, 0.1, 0.03, 0.4))
    # call_price(5.0, 5.0, 0.25, 0.03, 0.4, 99)
    print(call_iv(0.138, 3.046, 3.1, 0.5, r=0.03, sigma_min=0.01, sigma_max=1.0, e=0.00001, steps=100))


if __name__ == '__main__':
    my_test2()

