"""
Author: shifulin
Email: shifulin666@qq.com
"""
import time
import math
import datetime
from io import BytesIO
from copy import deepcopy

import numpy as np
import matplotlib.pyplot as plt

from sina_stock_kline_api import get_stock_day_kline
from sina_future_kline_api import get_future_day_kline
from sina_commodity_option_api import get_option_kline as get_future_option_day_kline
from sina_commodity_option_api import get_underlying_price
from sina_commodity_option_api import get_option_price as get_future_option_price
from sina_etf_option_api import get_option_day_kline as get_etf_option_day_kline
from sina_etf_option_api import get_option_price as get_etf_option_price
import european_option
import american_option


ETF_SPOT_CODE = {
    '510050': 'sh510050',
    '510300': 'sh510300',
}

STOCK_SPOT_CODE = deepcopy(ETF_SPOT_CODE)
STOCK_SPOT_CODE.update({
    '159919': 'sz159919',
    '000300': 'sh000300',
})


def days_interval(date1, date2):
    d1 = datetime.datetime.strptime(str(date1), "%Y%m%d")
    d2 = datetime.datetime.strptime(str(date2), "%Y%m%d")
    days = abs((d1 - d2).days)
    return days, float(days) / 365.0


def get_kline(option_code, spot_code):
    if spot_code in ETF_SPOT_CODE:
        option_kline = get_etf_option_day_kline(option_code)
    else:
        option_kline = get_future_option_day_kline(option_code)
    if spot_code in STOCK_SPOT_CODE:
        spot_kline = get_stock_day_kline(STOCK_SPOT_CODE[spot_code])
    else:
        spot_kline = get_future_day_kline(spot_code)
    return option_kline, spot_kline


def cal_hv(y, window_size):
    len_y = len(y)
    if len_y >= window_size:
        factor = math.sqrt(252)
        hv = [np.std(y[i: i + window_size]) * factor for i in range(len(y) - window_size + 1)]
        return [np.nan for _ in range(window_size)] + hv
    else:
        return [np.nan for _ in range(len_y + 1)]


def align_kline(option_kline, spot_kline, window_size):
    if not option_kline or not spot_kline:
        return [], []
    else:
        if 'c' in option_kline[0]:
            date_key, close_key, date_func = 'd', 'c', lambda x: int(''.join(x.split('-')))
        else:
            date_key, close_key, date_func = 'date', 'close', lambda x: int(''.join(x[:10].split('-')))
        option_data = [(date_func(i[date_key]), float(i[close_key])) for i in option_kline]
        if 'c' in spot_kline[0]:
            date_key, close_key, date_func = 'd', 'c', lambda x: int(''.join(x.split('-')))
        else:
            date_key, close_key, date_func = 'date', 'close', lambda x: int(''.join(x[:10].split('-')))
        tmp_hv, last_close = [], None
        for i in spot_kline:
            this_close = float(i[close_key])
            if last_close is not None:
                tmp_hv.append(math.log(this_close / last_close))
            last_close = this_close
        hv = cal_hv(tmp_hv, window_size)
        spot_data, spot_hv = [], []
        len_option_data = len(option_data)
        index = 0
        for k, h in zip(spot_kline, hv):
            k_date = date_func(k[date_key])
            op_date = option_data[index][0]
            while k_date > op_date:
                # print(f'Warning, miss option kline date: {k_date}', option_data[index])
                del option_data[index]
                len_option_data -= 1
                op_date = option_data[index][0]
            if k_date == op_date:
                spot_data.append((k_date, float(k[close_key])))
                spot_hv.append(h)
                index += 1
            else:
                if index >= len_option_data:
                    break
        # print(option_data)
        # print(spot_data)
        assert len_option_data == len(spot_data)
        return option_data, spot_data, spot_hv


def cal_historical_iv(option_kline, spot_kline, strike_price, expiry_date, r, option_type, exercise_type):
    if exercise_type == 'european':
        iv_func = european_option.call_iv if option_type == 'call' else european_option.put_iv
    else:
        iv_func = american_option.call_iv if option_type == 'call' else american_option.put_iv
    x, y = [], []
    for option, spot in zip(option_kline, spot_kline):
        x.append(str(option[0]))
        t = days_interval(option[0], expiry_date)[1]
        y.append(iv_func(option[1], spot[1], strike_price, t, r=r))
    return x, y


def draw_picture(option_code, x, iv, hv, last_iv, show=True):
    # print(len(x), len(iv), len(hv))
    interval = math.ceil(len(x) / 20)
    x_index = list(range(len(x)))[::-interval]
    x_label = x[::-interval]
    fig, axs = plt.subplots(3, sharex=True, gridspec_kw={'hspace': 0})
    gs = axs[0].get_gridspec()
    for ax in axs[0: 2]:
        ax.remove()
    ax0 = fig.add_subplot(gs[0: 2], sharex=axs[2])
    ax0.axhline(last_iv, color='purple', linestyle='--')
    ax0.plot(hv, 'darkorange')
    ax0.plot(iv, 'b', lw=2)
    ax0.set_xlim((0, len(x) - 1))
    ax0.grid()
    ax0.set_title(option_code)
    plt.setp(ax0.get_xticklabels(), visible=False)
    ax0.legend(['now iv', 'historical volatility', 'implied volatility'])
    axs[2].axhline(0, color='k', lw=1)
    axs[2].plot(np.array(hv) - np.array(iv), 'r')
    axs[2].set_xticks(x_index[::-1])
    axs[2].set_xticklabels(x_label[::-1], rotation=60)
    axs[2].set_xlim((0, len(x) - 1))
    axs[2].set_ylabel('hv - iv')
    axs[2].grid()
    fig.tight_layout()
    if show:
        plt.show()
    else:
        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        return buffer.getvalue()


def get_last_price(option_code, spot_code):
    if spot_code in STOCK_SPOT_CODE:
        spot_price = float(get_underlying_price(STOCK_SPOT_CODE[spot_code])[3])
        option_price = float(get_etf_option_price(option_code)[2][1])
    else:
        spot_price = float(get_underlying_price(spot_code.upper())[8])
        option_price = float(get_future_option_price(option_code)[2])
    return option_price, spot_price


def get_last_iv(option_price, spot_price, strike_price, expiry_date, option_type, exercise_type):
    today = time.strftime('%Y%m%d', time.localtime(time.time()))
    t = days_interval(today, expiry_date)[1]
    if exercise_type == 'european':
        iv_func = european_option.call_iv if option_type == 'call' else european_option.put_iv
    else:
        iv_func = american_option.call_iv if option_type == 'call' else american_option.put_iv
    return iv_func(option_price, spot_price, strike_price, t)


def main(option_code, spot_code, strike_price, expiry_date, option_type, exercise_type, window_size):
    option_kline, spot_kline = get_kline(option_code, spot_code)
    op_k, sp_k, hv = align_kline(option_kline, spot_kline, window_size=window_size)
    x, iv = cal_historical_iv(op_k, sp_k, strike_price, expiry_date, 0.03, option_type, exercise_type)
    option_price, spot_price = get_last_price(option_code, spot_code)
    last_iv = get_last_iv(option_price, spot_price, strike_price, expiry_date, option_type, exercise_type)
    draw_picture(option_code, x, iv, hv, last_iv)


if __name__ == '__main__':
    # main('cu2003C51000', 'cu2003', 51000.0, '20200224', 'call', 'european', 5)
    # main('au2004P340', 'au2004', 340.0, '20200325', 'put', 'european', 10)
    main('10002062', '510050', 3.0, '20200122', 'put', 'european', 15)
    # main('m2005C2800', 'm2005', 2800.0, '20200408', 'call', 'american', 5)
    # main('m2005P2700', 'm2005', 2700.0, '20200408', 'put', 'american', 10)
