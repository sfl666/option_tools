"""
Author: shifulin
Email: shifulin666@qq.com
"""
from math import log, sqrt, exp, inf
from scipy.stats import norm
import scipy.optimize as opt


def bsm_call(s, k, sigma, t, r, q):
    sqrt_t = sqrt(t)
    d1 = (log(s / k) + (r - q + sigma ** 2 / 2.0) * t) / (sigma * sqrt_t)
    d2 = d1 - sigma * sqrt_t
    return s * exp(-q * t) * norm.cdf(d1) - k * exp(-r * t) * norm.cdf(d2)


def bsm_put(s, k, sigma, t, r, q):
    sqrt_t = sqrt(t)
    d1 = (log(s / k) + (r - q + sigma ** 2 / 2.0) * t) / (sigma * sqrt_t)
    d2 = d1 - sigma * sqrt_t
    return k * exp(-r * t) * norm.cdf(-d2) - s * exp(-q * t) * norm.cdf(-d1)


def find_sx(sx, k, sigma, t, r, q, option_type):
    n = 2.0 * (r - q) / sigma ** 2
    k_ = 2.0 * r / sigma ** 2 / (1.0 - exp(-r * t))
    if sx < 0.0:
        return inf
    if option_type == 'Call':
        q2 = (1.0 - n + sqrt((n - 1.0) ** 2 + 4.0 * k_)) / 2.0
        return (bsm_call(sx, k, sigma, t, r, q) + (1.0 - exp(-q * t)
                * norm.cdf((log(sx / k) + (r - q + sigma ** 2 / 2.0)) / (sigma * sqrt(t))))
                * sx / q2 - sx + k) ** 2
    else:
        q1 = (1.0 - n - sqrt((n - 1.0) ** 2 + 4.0 * k_)) / 2.0
        return (bsm_put(sx, k, sigma, t, r, q) - (1.0 - exp(-q * t)
                * norm.cdf(-(log(sx / k) + (r - q + sigma ** 2 / 2.0)) / (sigma * sqrt(t))))
                * sx / q1 + sx - k) ** 2


def baw_call(s, k, sigma, t, r, q=0.0):
    c = bsm_call(s, k, sigma, t, r, q)
    sx = opt.fmin(lambda i: find_sx(i, k, sigma, t, r, q, 'Call'), s)[0]
    d1 = (log(sx / k) + (r - q + sigma ** 2 / 2.0)) / (sigma * sqrt(t))
    n = 2.0 * (r - q) / sigma ** 2.0
    k_ = 2.0 * r / (sigma ** 2 * (1.0 - exp(-r * t)))
    q2 = (1.0 - n + sqrt((n - 1.0) ** 2 + 4.0 * k_)) / 2.0
    a2 = sx * (1.0 - exp(-q * t) * norm.cdf(d1)) / q2
    return c + a2 * (s / sx) ** q2 if s < sx else s - k


def baw_put(s, k, sigma, t, r, q=0.0):
    p = bsm_put(s, k, sigma, t, r, q)
    sx = opt.fmin(lambda i: find_sx(i, k, sigma, t, r, q, 'Put'), s)[0]
    d1 = (log(sx / k) + (r - q + sigma ** 2 / 2.0)) / (sigma * sqrt(t))
    n = 2.0 * (r - q) / sigma ** 2
    k_ = 2.0 * r / (sigma ** 2 * (1.0 - exp(-r * t)))
    q1 = (1.0 - n - sqrt((n - 1.0) ** 2 + 4.0 * k_)) / 2.0
    a1 = -sx * (1.0 - exp(-q * t) * norm.cdf(-d1)) / q1
    return p + a1 * (s / sx) ** q1 if s > sx else k - s


def call_iv(c, s, k, t, r=0.03, sigma_min=0.0001, sigma_max=3.0, e=0.00001):
    sigma_mid = (sigma_min + sigma_max) / 2.0
    call_min = bsm_call(s, k, sigma_min, t, r, 0.0)
    call_max = bsm_call(s, k, sigma_max, t, r, 0.0)
    call_mid = bsm_call(s, k, sigma_mid, t, r, 0.0)
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
        call_mid = bsm_call(s, k, sigma_mid, t, r, 0.0)
        diff = c - call_mid
    return sigma_mid


def put_iv(c, s, k, t, r=0.03, sigma_min=0.0001, sigma_max=3.0, e=0.00001):
    sigma_mid = (sigma_min + sigma_max) / 2.0
    put_min = bsm_put(s, k, sigma_min, t, r, 0.0)
    put_max = bsm_put(s, k, sigma_max, t, r, 0.0)
    put_mid = bsm_put(s, k, sigma_mid, t, r, 0.0)
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
        put_mid = bsm_put(s, k, sigma_mid, t, r, 0.0)
        diff = c - put_mid
    return sigma_mid


def delta(s, k, sigma, t, r, option_type):
    if t == 0.0:
        if s == k:
            return 0.5 if option_type == 'Call' else -0.5
        elif s > k:
            return 1.0 if option_type == 'Call' else 0.0
        else:
            return 0.0 if option_type == 'Call' else -1.0
    else:
        price_func = baw_call if option_type == 'Call' else baw_put
        return (price_func(s + 0.01, k, sigma, t, r) -
                price_func(s - 0.01, k, sigma, t, r)) * 50.0


def gamma(s, k, sigma, t, r, option_type):
    if t == 0.0:
        return inf if s == k else 0.0
    price_func = baw_call if option_type == 'Call' else baw_put
    return (price_func(s + 0.01, k, sigma, t, r) +
            price_func(s - 0.01, k, sigma, t, r) -
            price_func(s, k, sigma, t, r) * 2.0) * 10000.0


def theta(s, k, sigma, t, r, option_type):
    price_func = baw_call if option_type == 'Call' else baw_put
    t_unit = 1.0 / 365.0
    if t <= t_unit:
        return price_func(s, k, sigma, 0.0001, r) - \
               price_func(s, k, sigma, t, r)
    else:
        return price_func(s, k, sigma, t - t_unit, r) - \
               price_func(s, k, sigma, t, r)


def vega(s, k, sigma, t, r, option_type):
    price_func = baw_call if option_type == 'Call' else baw_put
    if sigma < 0.02:
        return 0.0
    else:
        return (price_func(s, k, sigma + 0.01, t, r) -
                price_func(s, k, sigma - 0.01, t, r)) * 50.0


def rho(s, k, sigma, t, r, option_type):
    price_func = baw_call if option_type == 'Call' else baw_put
    return (price_func(s, k, sigma, t, r + 0.001,) -
            price_func(s, k, sigma, t, r - 0.001,)) * 500.0


if __name__ == '__main__':
    # print(baw_call(2707, 2900, 0.165, 78.0 / 365, 0.03, 0.0))
    # print(baw_put(2710, 2750, 0.15, 78.0 / 365, 0.03, 0.0))
    print(call_iv(24.0, 2710, 2900, 78.0 / 365))
    print(put_iv(92.5, 2710, 2750, 78.0 / 365))

