"""
Author: shifulin
Email: shifulin666@qq.com
"""
import time
from threading import Thread, Lock
from collections import namedtuple
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from mpl_toolkits.mplot3d import Axes3D

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
        self.x_index = []
        self.spot_price = 0.0
        self.update_picture_lock = Lock()
        self.elev = 30
        self.azim = 120
        self.colors = ['blue', 'yellow', 'lime', 'red', 'purple', 'slategray', 'tomato', 'orange', 'darkred', 'aqua']
        self.init()
        self.lines = {}
        self.update_price(self.get_spot_price(), self.get_option_price())

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
                index = 5
                iv_func = european_option.put_iv
            self.data[x, y, index] = price
            iv = iv_func(price, spot_price, k, t)
            delta, gamma, theta, vega = european_option.greeks(spot_price, k, iv, 0.03, t, option_type)
            self.data[x, y, index] = delta
            self.data[x, y, index + 1] = gamma
            self.data[x, y, index + 2] = theta
            self.data[x, y, index + 3] = vega
            self.data[x, y, index + 4] = iv

    def init(self):
        strike_prices, expiry_dates = set(), set()
        data = self.get_option_price()
        for i in data:
            strike_prices.add(i[7])
            expiry_dates.add(i[-1][2:6])
        self.strike_prices = sorted(strike_prices, key=lambda i: float(i))
        self.expiry_dates = sorted(expiry_dates, key=lambda i: int(i))
        self.x_index = [float(i) for i in self.strike_prices]
        strike_prices = {j: i for i, j in enumerate(self.strike_prices)}
        expiry_dates = {j: i for i, j in enumerate(self.expiry_dates)}
        for i in data:
            x = strike_prices[i[7]]
            y = expiry_dates[i[-1][2:6]]
            k = float(i[7])
            t = float(self.expiry_date_map[i[-1][2:6]]) / 365.0
            option_type = 'Call' if 'C' in i[-1] else 'Put'
            self.code_to_info[i[-1]] = OptionInfo(x, y, k, t, option_type)
        self.x, self.y = np.meshgrid(list(range(len(expiry_dates))), [float(i) for i in strike_prices])
        self.data = np.ones(self.x.shape + (10, ))
        for i in self.code_to_info.values():
            self.data[i.x, i.y, :] = 0.0
        self.data[self.data > 0.5] = np.nan

    def start_update_picture(self):
        fig = plt.figure(figsize=(12, 5.7))
        fig.canvas.mpl_connect('button_press_event', lambda event: self.update_picture_lock.acquire())
        fig.canvas.mpl_connect('button_release_event', lambda event: self.update_picture_lock.release())
        gs = gridspec.GridSpec(3, 6, figure=fig)
        call_gs = [gs[2:3, :1], gs[2:3, 1:2], gs[2:3, 2:3], gs[1:2, 2:3], gs[:1, 2:3]]
        put_gs = [gs[2:3, 3:4], gs[2:3, 4:5], gs[2:3, 5:6], gs[1:2, 5:6], gs[:1, 5:6]]
        ylabels = ['Delta', 'Gamma', 'Theta', 'Vega', 'Implied Volatility']
        m, n, _ = self.data.shape
        for index in range(5):
            call_ax = fig.add_subplot(call_gs[index])
            tmp = []
            for i in range(n):
                line, = call_ax.plot(self.x_index, self.data[:, i, index], self.colors[i])
                tmp.append(line)
            self.lines[call_ax] = (index, tmp)
            call_ax.set_xlabel('Strike Price')
            call_ax.set_ylabel(ylabels[index])
            call_ax.legend(self.expiry_dates, fontsize='xx-small')
            put_ax = fig.add_subplot(put_gs[index])
            tmp = []
            for i in range(n):
                line, = put_ax.plot(self.x_index, self.data[:, i, index + 5], self.colors[i])
                tmp.append(line)
            self.lines[put_ax] = (index + 5, tmp)
            put_ax.set_xlabel('Strike Price')
            put_ax.set_ylabel(ylabels[index])
            put_ax.legend(self.expiry_dates, fontsize='xx-small')
        ax_iv_sf_call = fig.add_subplot(gs[:2, :2], projection='3d')
        self.surf_call = ax_iv_sf_call.plot_wireframe(self.x, self.y, self.data[:, :, 4], rstride=1, cstride=1)
        ax_iv_sf_call.set_yticklabels(self.expiry_dates)
        ax_iv_sf_call.set_xlabel('Strike Price')
        ax_iv_sf_call.set_ylabel('Expiration Date')
        ax_iv_sf_call.set_zlabel('Implied Volatility')
        ax_iv_sf_call.set_title('Call Option')
        ax_iv_sf_call.view_init(self.elev, self.azim)
        ax_iv_sf_put = fig.add_subplot(gs[:2, 3:5], projection='3d')
        self.surf_put = ax_iv_sf_put.plot_wireframe(self.x, self.y, self.data[:, :, 9], rstride=1, cstride=1)
        ax_iv_sf_put.set_yticklabels(self.expiry_dates)
        ax_iv_sf_put.set_xlabel('Strike Price')
        ax_iv_sf_put.set_ylabel('Expiration Date')
        ax_iv_sf_put.set_zlabel('Implied Volatility')
        ax_iv_sf_put.set_title('Put Option')
        ax_iv_sf_put.view_init(self.elev, self.azim)

        def update_picture():
            while True:
                with self.update_picture_lock:
                    self.azim += 15
                    if self.azim > 360:
                        self.azim -= 360
                    for k, v in self.lines.items():
                        index, lines = v
                        [k.lines.remove(lines[i]) for i in range(n)]
                        tmp = []
                        for i in range(n):
                            line, = k.plot(self.x_index, self.data[:, i, index], self.colors[i])
                            tmp.append(line)
                        self.lines[k] = (index, tmp)
                    self.surf_call.remove()
                    self.surf_call = ax_iv_sf_call.plot_wireframe(self.x, self.y, self.data[:, :, 4], rstride=1, cstride=1)
                    ax_iv_sf_call.view_init(self.elev, self.azim)
                    self.surf_put.remove()
                    self.surf_put = ax_iv_sf_put.plot_wireframe(self.x, self.y, self.data[:, :, 9], rstride=1, cstride=1)
                    ax_iv_sf_put.view_init(self.elev, self.azim)
                    plt.draw()
                    plt.tight_layout()
                time.sleep(5)
                self.update_price(self.get_spot_price(), self.get_option_price())
        t = Thread(target=update_picture)
        t.setDaemon(True)
        t.start()
        plt.show()

    def draw_picture(self):
        pass


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
    vs.start_update_picture()


if __name__ == '__main__':
    main()
