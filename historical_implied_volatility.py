"""
Author: shifulin
Email: shifulin666@qq.com
"""
import math
import datetime
from io import BytesIO
from copy import deepcopy

import matplotlib.pyplot as plt

from sina_stock_kline_api import get_stock_day_kline
from sina_future_kline_api import get_future_day_kline
from sina_commodity_option_api import get_option_kline as get_future_option_day_kline
from sina_etf_option_api import get_option_day_kline as get_etf_option_day_kline
import european_option
# import american_option
import baw


ETF_SPOT_CODE = {
    '510050': 'sh510050',
    '510300': 'sh510300',
    '159919': 'sz159919',
}

STOCK_SPOT_CODE = deepcopy(ETF_SPOT_CODE)
STOCK_SPOT_CODE.update({
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


def align_kline(option_kline, spot_kline):
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
        spot_data, option_data2 = [], []
        len_option_data = len(option_data)
        index = 0
        for k in spot_kline:
            k_date = date_func(k[date_key])
            op_date = option_data[index][0]
            while k_date > op_date:
                # print(f'Warning, miss option kline date: {k_date}', option_data[index])
                index += 1
                op_date = option_data[index][0]
            if k_date == op_date:
                spot_data.append((k_date, float(k[close_key])))
                option_data2.append(option_data[index])
                index += 1
            if index >= len_option_data:
                break
        # print(option_data)
        # print(spot_data)
        return option_data2, spot_data


def cal_historical_iv(option_kline, spot_kline, strike_price, expiry_date, r, option_type, exercise_type):
    if exercise_type == 'european':
        iv_func = european_option.call_iv if option_type == 'Call' else european_option.put_iv
    else:
        iv_func = baw.call_iv if option_type == 'Call' else baw.put_iv
    x, y, option_cp, spot_cp = [], [], [], []
    for option, spot in zip(option_kline, spot_kline):
        x.append(str(option[0]))
        t = days_interval(option[0], expiry_date)[1]
        y.append(iv_func(option[1], spot[1], strike_price, t, r=r))
        option_cp.append(option[1])
        spot_cp.append(spot[1])
    return x, y, option_cp, spot_cp


def draw_picture(option_code, x, iv, option_cp, spot_cp, show=True):
    interval = math.ceil(len(x) / 20)
    real_x = list(range(len(x)))
    x_index = real_x[::-interval]
    x_label = x[::-interval]
    fig, axs = plt.subplots(2, sharex=True, gridspec_kw={'hspace': 0}, figsize=(12.0, 5.7))
    axs[0].plot(iv, color='r')
    axs[0].set_xlim((real_x[0], real_x[-1]))
    axs[0].set_ylabel('Implied Volatility')
    axs[0].set_title(option_code)
    axs[0].grid()
    line1 = axs[1].plot(option_cp, 'blue', label='option')
    ax2 = axs[1].twinx()
    line2 = ax2.plot(spot_cp, 'orange', label='spot')
    axs[1].set_xticks(x_index[::-1])
    axs[1].set_xticklabels(x_label[::-1], rotation=60)
    axs[1].set_ylabel('Price')
    axs[1].grid()
    lines = line1 + line2
    line_labels = [i.get_label() for i in lines]
    axs[1].legend(lines, line_labels, loc=0)
    plt.tight_layout()
    if show:
        plt.show()
    else:
        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        return buffer.getvalue()


def main(option_code, spot_code, strike_price, expiry_date, option_type, exercise_type):
    option_kline, spot_kline = get_kline(option_code, spot_code)
    op_k, sp_k = align_kline(option_kline, spot_kline)
    x, iv, option_cp, spot_cp = cal_historical_iv(op_k, sp_k, strike_price, expiry_date, 0.03, option_type, exercise_type)
    draw_picture(option_code, x, iv, option_cp, spot_cp)


if __name__ == '__main__':
    # main('cu2003C51000', 'cu2003', 51000.0, '20200224', 'Call', 'european')
    # main('au2004P340', 'au2004', 340.0, '20200325', 'Put', 'european')
    # main('io2002C4050', '000300', 4050.0, '20200221', 'Call', 'european')
    # main('10002194', '510050', 3.1, '20200226', 'Call', 'european')
    # main('m2005C2800', 'm2005', 2800.0, '20200408', 'Call', 'american')
    main('m2005P2600', 'm2005', 2600.0, '20200408', 'Put', 'american')
    # main('ta2005P4800', 'ta2005', 4800.0, '20200403', 'Put', 'american')
