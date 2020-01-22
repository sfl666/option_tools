"""
Author: shifulin
Email: shifulin666@qq.com
"""
import math
from io import BytesIO
import numpy as np
import matplotlib.pyplot as plt
from sina_stock_kline_api import get_stock_day_kline, get_ex_data
from sina_future_kline_api import get_future_day_kline


ETF_SPOT_MAP = {
    'sh510050': 'sh000016',
    'sh510300': 'sh000300',
    'sz159919': 'sh000300',
}


def cal_stock_fluctuation(code, kline, ex):
    x, y = [], []
    kline_data = kline[code]
    for index, i in enumerate(kline_data):
        if index > 0:
            y.append(math.log(i['close'] / kline_data[index - 1]['close']))
            x.append(int(''.join(i['date'][:10].split('-'))))
    if code in ETF_SPOT_MAP:
        listed_date = int(''.join(kline_data[0]['date'][:10].split('-')))
        ex_date = [int(''.join(i['djr'][:10].split('-'))) for i in ex[code] if i['djr']]
        ex_date = [i for i in ex_date if i > listed_date][::-1]
        ex_result = {}
        if ex_date:
            spot_kline = kline[ETF_SPOT_MAP[code]]
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


def get_stock_data(code):
    kline = {code: get_stock_day_kline(code)}
    if code in ETF_SPOT_MAP:
        kline[ETF_SPOT_MAP[code]] = get_stock_day_kline(ETF_SPOT_MAP[code])
        ex = {code: get_ex_data(code)}
    else:
        ex = {code: []}
    return cal_stock_fluctuation(code, kline, ex)


def cal_future_fluctuation(kline):
    x, y = [], []
    if kline:
        last_close = float(kline[0]['c'])
        for k in kline[1:]:
            x.append(int(''.join(k['d'].split('-'))))
            close = float(k['c'])
            y.append(math.log(close / last_close))
            last_close = close
    return x, y


def get_future_data(code):
    return cal_future_fluctuation(get_future_day_kline(code))


def cal_historical_volatility(y, window_size):
    y2 = y[::-1]
    hv_lines, hv_cone = [], []
    factor = np.sqrt(252) * 100.0
    for w in window_size:
        hv = [np.std(y2[i: i + w]) * factor for i in range(len(y2) - w + 1)]
        hv_lines.append(hv)
        # hv_cone.append((max(hv), np.percentile(hv, 75), np.median(hv), np.percentile(hv, 25), min(hv), hv[0]))
    return hv_lines, hv_cone


def draw_picture(code, x, y, interval, window_size, show=True):
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
    xticks = x[-len(hv_lines[0]):][::-interval][::-1]
    xticks_index = x_hv[::-interval][::-1]
    axs2[1].set_xticks(xticks_index)
    axs2[1].set_xticklabels([str(i) for i in xticks], rotation=60)
    axs2[1].set_ylabel('historical volatility(%)')
    axs2[1].set_xlabel(f'historical volatility of {code} in different window size')
    plt.tight_layout()
    if show:
        plt.show()
    else:
        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        return buffer.getvalue()


def main(code, security_type='stock', window_size=(5, 15, 30, 50, 70, 90, 120, 150)):
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
    if security_type == 'stock':
        x, y = get_stock_data(code)
    elif security_type == 'future':
        x, y = get_future_data(code)
    else:
        return
    interval = math.ceil(len(x) / 20)
    draw_picture(code, x, y, interval, window_size, show=True)


if __name__ == '__main__':
    # main('sz159919')
    # main('sh000300')
    main('m2005', security_type='future', window_size=(5, 15, 30, 50, 90, 120))

