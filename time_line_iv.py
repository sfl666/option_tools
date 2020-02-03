"""
Author: shifulin
Email: shifulin666@qq.com
"""
import math
from io import BytesIO
import matplotlib.pyplot as plt
from sina_etf_option_api import get_option_time_line as get_etf_option_time_line
from sina_stock_kline_api import get_stock_time_line, get_1minutes
import european_option as european_option


SPOT_CODE_MAP = {
    '510050': 'sh510050',
    '510300': 'sh510300',
}


def get_data(option_code, spot_code):
    option_line = get_etf_option_time_line(option_code)
    spot_line = get_stock_time_line(spot_code)
    return option_line, spot_line


def time_str_to_int(time_str):
    return int(''.join(time_str.split(':')[:2]))


def align_line(option_line, spot_line):
    times, option_price, spot_price = [], [], []
    if not option_line or not spot_line:
        return times, option_price, spot_price
    index = 0
    len_option_line = len(option_line)
    for i in spot_line:
        spot_time = time_str_to_int(i[3])
        option_time = time_str_to_int(option_line[index]['i'])
        while spot_time > option_time and index < len_option_line - 1:
            index += 1
            # print('#########', len(option_line), len(spot_line), index)
            option_time = time_str_to_int(option_line[index]['i'])
        if spot_time == option_time:
            times.append(i[3])
            spot_price.append(i[1] if i[1] > 0.00001 else math.nan)
            tmp_price = float(option_line[index]['p'])
            option_price.append(tmp_price if tmp_price > 0.00001 else math.nan)
    return times, option_price, spot_price


def cal_iv(option_price, spot_price, k, t, option_type):
    iv_func = european_option.call_iv if option_type == 'Call' else european_option.put_iv
    return [iv_func(i, j, k, t) if (i > 0.00001 and j > 0.00001) else math.nan for i, j in zip(option_price, spot_price)]


def draw_picture(times, option_price, spot_price, iv, option_code, show=True):
    interval = math.ceil(len(times) / 20.0)
    x = list(range(len(times)))
    fig, axs = plt.subplots(2, sharex=True, gridspec_kw={'hspace': 0}, figsize=(12.0, 5.7))
    axs[0].plot(iv, color='r')
    axs[0].set_xlim((x[0], x[-1]))
    axs[0].set_ylabel('Implied Volatility')
    axs[0].set_title(option_code)
    axs[0].grid()
    line1 = axs[1].plot(option_price, 'blue', label='option')
    ax2 = axs[1].twinx()
    line2 = ax2.plot(spot_price, 'orange', label='spot')
    axs[1].set_xticks(x[::-interval][::-1])
    axs[1].set_xticklabels(times[::-interval][::-1], rotation=60)
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


def main(option_code, spot_code, k, t, option_type, show=True):
    if spot_code in SPOT_CODE_MAP:
        spot_code = SPOT_CODE_MAP[spot_code]
    else:
        return ''
    times, option_price, spot_price = align_line(*get_data(option_code, spot_code))
    iv = cal_iv(option_price, spot_price, k, t, option_type)
    return draw_picture(times, option_price, spot_price, iv, option_code, show)


if __name__ == '__main__':
    main('10002235', '510050', 3.0, 238.0 / 365.0, 'Call')

