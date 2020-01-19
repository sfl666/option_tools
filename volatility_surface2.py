"""
Author: shifulin
Email: shifulin666@qq.com
"""
import time
from collections import namedtuple
import numpy as np

from sina_commodity_option_api import get_000300_price, get_t_quotation
import european_option

# EUROPEAN_OPTION = {'io', 'cu', 'au'}
OptionInfo = namedtuple('OptionInfo', ['x', 'y', 'k', 't', 'type'])


class VolSurface(object):
    def __init__(self, expiry_date_map):
        self.spot = 'io'
        self.expiry_date_map = expiry_date_map
        self.x = np.array([[[]]])
        self.y = np.array([[[]]])
        self.data = np.array([[[]]])
        self.code_to_info = {}
        self.strike_prices = []
        self.expiry_dates = []
        self.spot_price = 0.0
        self.init()

    @staticmethod
    def get_spot_price():
        return float(get_000300_price()[3])

    def get_option_price(self):
        result = []
        for i in self.expiry_date_map:
            up, down = get_t_quotation(self.spot + i)
            result.extend(up)
            result.extend(down)
        return result

    def update_price(self, spot_price, option_price):
        self.spot_price = spot_price
        for i in option_price:
            price = (float(i[1]) + float(i[3])) / 2.0
            x, y, k, t, option_type = self.code_to_info[i[-1]]
            if option_type == 'Call':
                index = 0
                iv_func = european_option.call_iv
            else:
                index = 6
                iv_func = european_option.put_iv
            self.data[x, y, index] = price
            iv = iv_func(price, spot_price, k, t)
            delta, gamma, theta, vega = european_option.greeks(spot_price, k, iv, 0.03, t, option_type)
            self.data[x, y, index + 1] = iv
            self.data[x, y, index + 2] = delta
            self.data[x, y, index + 3] = gamma
            self.data[x, y, index + 4] = theta
            self.data[x, y, index + 5] = vega
            # print(iv, delta, gamma, theta, vega)

    def init(self):
        strike_prices, expiry_dates = set(), set()
        data = self.get_option_price()
        for i in data:
            strike_prices.add(i[7])
            expiry_dates.add(i[-1][2:6])
        self.strike_prices = sorted(strike_prices, key=lambda i: float(i))
        self.expiry_dates = sorted(expiry_dates, key=lambda i: int(i))
        # print(self.strike_prices)
        # print(self.expiry_dates)
        strike_prices = {j: i for i, j in enumerate(self.strike_prices)}
        expiry_dates = {j: i for i, j in enumerate(self.expiry_dates)}
        for i in data:
            # print(i)
            x = strike_prices[i[7]]
            y = expiry_dates[i[-1][2:6]]
            k = float(i[7])
            t = float(self.expiry_date_map[i[-1][2:6]]) / 365.0
            option_type = 'Call' if 'C' in i[-1] else 'Put'
            self.code_to_info[i[-1]] = OptionInfo(x, y, k, t, option_type)
        self.x, self.y = np.meshgrid(list(range(len(expiry_dates))), list(range(len(strike_prices))))
        self.data = np.ones(self.x.shape + (12, ))
        # print(self.x.shape, self.y.shape, self.data.shape)
        # print(len(strike_prices), len(expiry_dates))
        for i in self.code_to_info.values():
            self.data[i.x, i.y, :] = 0.0
        self.data[self.data > 0.5] = np.nan
        # print(self.x)
        # print(self.y)


def main():
    expiry_date_map = {
        '2002': 33,
        '2003': 61,
        '2004': 89,
        '2006': 152,
        '2009': 243,
        '2012': 334,
    }
    vs = VolSurface(expiry_date_map)
    a = time.clock()
    vs.update_price(vs.get_spot_price(), vs.get_option_price())
    b = time.clock()
    print('---------------', b-a)


if __name__ == '__main__':
    main()
