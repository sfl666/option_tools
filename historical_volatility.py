"""
Author: shifulin
Email: shifulin666@qq.com
"""
import math
import numpy as np
import matplotlib.pyplot as plt
from sina_stock_kline_api import get_stock_day_kline, get_ex_data


ETF_SPOT_MAP = {
    'sh510050': 'sh000016',
    'sh510300': 'sh000300',
    'sz159919': 'sh000300',
}


def get_stock_data(code):
    x, y = [], []
    kline_data = get_stock_day_kline(code)
    for index, i in enumerate(kline_data):
        if index > 0:
            y.append(math.log(i['close'] / kline_data[index - 1]['close']))
            x.append(int(''.join(i['date'][:10].split('-'))))
    # print(x)
    # print(y)
    if code in ETF_SPOT_MAP:
        listed_date = int(''.join(kline_data[0]['date'][:10].split('-')))
        # ex_data = get_ex_data(code)
        ex_date = [int(''.join(i['djr'][:10].split('-'))) for i in get_ex_data(code) if i['djr']]
        ex_date = [i for i in ex_date if i > listed_date][::-1]
        # print(ex_date)
        # print(listed_date)
        ex_result = {}
        if ex_date:
            spot_kline = get_stock_day_kline(ETF_SPOT_MAP[code])
            last_date, last_close = 0, 0.0
            for index, i in enumerate(spot_kline):
                this_date = int(''.join(i['date'][:10].split('-')))
                if index > 0:
                    if last_date <= ex_date[0] < this_date:
                        ex_result[this_date] = math.log(i['close'] / last_close)
                        ex_date = ex_date[1:]
                        if not ex_date:
                            break
                last_date = this_date
                last_close = i['close']
        # print(ex_result)
        for index, i in enumerate(x):
            if i in ex_result:
                # print(i, y[index], ex_result[i])
                y[index] = ex_result[i]
    return x, y


def cal_historical_volatility(y, window_size):
    y2 = y[::-1]
    hv_lines, hv_cone = [], []
    factor = np.sqrt(252) * 100.0
    for w in window_size:
        hv = [np.std(y2[i: i + w]) * factor for i in range(len(y2) - w + 1)]
        hv_lines.append(hv)
        hv_cone.append((max(hv), np.percentile(hv, 75), np.median(hv), np.percentile(hv, 25), min(hv), hv[0]))
    return hv_lines, hv_cone


def main(code, window_size=(5, 15, 30, 50, 70, 90, 120, 150)):
    # import pickle, os
    # if os.path.isfile('cache'):
    #     with open('cache', 'rb') as fp:
    #         x = pickle.load(fp)
    #         y = pickle.load(fp)
    #         hv_lines = pickle.load(fp)
    #         hv_cone = pickle.load(fp)
    # else:
    #     x, y = get_stock_data(code)
    #     hv_lines, hv_cone = cal_historical_volatility(y, window_size)
    #     with open('cache', 'wb') as fp:
    #         pickle.dump(x, fp)
    #         pickle.dump(y, fp)
    #         pickle.dump(hv_lines, fp)
    #         pickle.dump(hv_cone, fp)
    x, y = get_stock_data(code)
    hv_lines, hv_cone = cal_historical_volatility(y, window_size)
    x_int = list(range(len(x)))
    len_window = len(window_size)
    fig, axs = plt.subplots(2, len_window, sharey=True, gridspec_kw={'hspace': 0, 'wspace': 0}, figsize=(13, 6.4))
    ylim = None
    for i in range(len_window):
        axs[0, i].hist(hv_lines[i], orientation='horizontal', bins=30, alpha=0.6, color='Orange')
        axs[0, i].axhline(hv_lines[i][0], color='r')
        axs[0, i].set_title(str(window_size[i]))
        if ylim is None:
            ylim = axs[0, i].get_ylim()
        else:
            axs[0, i].set_ylim(ylim)
        axs[0, i].get_xaxis().set_visible(False)
        axs[1, i].axis('off')
    axs[0, 0].set_ylabel('historical volatility(%)')
    axs2 = fig.subplots(2, 1, gridspec_kw={'hspace': 0, 'wspace': 0})
    axs2[0].axis('off')
    for hv in hv_lines:
        x_hv = x_int[-len(hv):]
        axs2[1].plot(x_hv, hv[::-1])
    x_hv = x_int[-len(hv_lines[0]):]
    axs2[1].set_xlim((min(x_hv), max(x_hv)))
    axs2[1].legend([str(i) for i in window_size])
    xticks = x[-len(hv_lines[0]):][::-100][::-1]
    xticks_index = x_hv[::-100][::-1]
    axs2[1].set_xticks(xticks_index)
    axs2[1].set_xticklabels([str(i) for i in xticks], rotation=60)
    axs2[1].set_ylabel('historical volatility(%)')
    axs2[1].set_xlabel(f'historical volatility of {code} in different window size')
    plt.tight_layout()
    plt.show()


if __name__ == '__main__':
    main('sz159919')


