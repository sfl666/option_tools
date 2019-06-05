"""
Author: shifulin
Email: shifulin666@qq.com
"""
# python3

from time import sleep
from threading import Thread

from requests import get, exceptions
from numpy import polyfit, polyval, meshgrid, array
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from mpl_toolkits.mplot3d import Axes3D

import sina_op_api

COLORS = ['blue', 'yellow', 'lime', 'red', 'purple', 'slategray', 'tomato', 'orange', 'darkred', 'aqua']
global_ax_lines_call = [{'ax': None, 'lines': []} for _ in range(5)]
global_ax_lines_put = [{'ax': None, 'lines': []} for _ in range(5)]
ELEV = 30


def requests_get(all_codes):
    url = "http://hq.sinajs.cn/list={codes}".format(codes=all_codes)
    while True:
        try:
            data = get(url).content.decode('gbk').strip().split('\n')
            break
        except (exceptions.ConnectionError, exceptions.ConnectTimeout) as e:
            print('连接出错，10秒后重试')
            print(e)
            sleep(10)
    return [i.split(',') for i in data]


def get_codes():
    while True:
        try:
            dates = sorted(sina_op_api.get_op_dates())
            call, put = [], []
            for date in dates:
                call_codes, put_codes = sina_op_api.get_op_codes(date)
                call.append(['CON_SO_' + i for i in call_codes])
                put.append(['CON_SO_' + i for i in put_codes])
            all_codes = ','.join([','.join(i) for i in call] + [','.join(i) for i in put])
            data = requests_get(all_codes)
            not_a_codes = [i[0][11:26] for i in data if not i[0].endswith('A')]  # 不考虑分红的
            for i in range(len(call)):
                call[i] = [j for j in call[i] if j in not_a_codes]
                put[i] = [j for j in put[i] if j in not_a_codes]
            break
        except (exceptions.ConnectionError, exceptions.ConnectTimeout) as e:
            print('连接出错，10秒后重试')
            print(e)
            sleep(10)
    return call, put, ','.join(not_a_codes), dates


def get_data(call, put, all_codes):
    implied_volatility, strike_price, vega, theta, gamma, delta = [], [], [], [], [], []
    for line in requests_get(all_codes):
        implied_volatility.append(float(line[9]))
        vega.append(float(line[8]))
        strike_price.append(float(line[13]))
        theta.append(float(line[7]))
        gamma.append(float(line[6]))
        delta.append(float(line[5]))
    call_implied_volatility, call_strike_price, call_vega, call_theta, call_gamma, call_delta = [], [], [], [], [], []
    put_implied_volatility, put_strike_price, put_vega, put_theta, put_gamma, put_delta = [], [], [], [], [], []
    b = 0
    for i in call:
        len_i = len(i)
        call_implied_volatility.append(implied_volatility[b:b + len_i])
        call_strike_price.append(strike_price[b:b + len_i])
        call_vega.append(vega[b:b + len_i])
        call_theta.append(theta[b:b + len_i])
        call_gamma.append(gamma[b:b + len_i])
        call_delta.append(delta[b:b + len_i])
        b += len_i
    for i in put:
        len_i = len(i)
        put_implied_volatility.append(implied_volatility[b:b + len_i])
        put_strike_price.append(strike_price[b:b + len_i])
        put_vega.append(vega[b:b + len_i])
        put_theta.append(theta[b:b + len_i])
        put_gamma.append(gamma[b:b + len_i])
        put_delta.append(delta[b:b + len_i])
        b += len_i
    return call_strike_price, [call_delta, call_gamma, call_theta, call_vega, call_implied_volatility], \
        put_strike_price, [put_delta, put_gamma, put_theta, put_vega, put_implied_volatility]


def fit(call_x, call_y, put_x, put_y):
    xx = set()
    for i in call_x:
        xx |= set(i)
    xx = sorted(xx)
    call_y2, put_y2 = [], []
    for i in range(len(call_x)):
        if xx == call_x[i]:
            call_y2.append(call_y[i])
        else:
            call_y2.append(polyval(polyfit(call_x[i], call_y[i], 2), xx))
        if xx == put_x[i]:
            put_y2.append(put_y[i])
        else:
            put_y2.append(polyval(polyfit(put_x[i], put_y[i], 2), xx))
    return xx, call_y2, put_y2


def update(call_codes, put_codes, all_codes, x, y, yy, surf_call, surf_put, ax_iv_sf_call, ax_iv_sf_put):
    azim = 15
    while True:
        sleep(3)  # 每隔3秒刷新一次
        call_x, call_ys, put_x, put_ys = get_data(call_codes, put_codes, all_codes)
        xx, call_y2, put_y2 = fit(call_x, call_ys[-1], put_x, put_ys[-1])
        surf_call.remove()
        azim += 15
        if azim > 360:
            azim = 0
        ax_iv_sf_call.view_init(ELEV, azim)
        surf_call = ax_iv_sf_call.plot_surface(x, y, array(call_y2), rstride=1, cstride=1, cmap='rainbow')
        surf_put.remove()
        ax_iv_sf_put.view_init(ELEV, azim)
        surf_put = ax_iv_sf_put.plot_surface(x, y, array(put_y2), rstride=1, cstride=1, cmap='rainbow')
        for index in range(5):
            for i in yy:
                global_ax_lines_call[index]['ax'].lines.remove(global_ax_lines_call[index]['lines'][i])
                global_ax_lines_put[index]['ax'].lines.remove(global_ax_lines_put[index]['lines'][i])
            global_ax_lines_call[index]['lines'] = []
            global_ax_lines_put[index]['lines'] = []
        for index in range(5):
            for i in yy:
                global_ax_lines_call[index]['lines'].append(global_ax_lines_call[index]['ax'].plot(call_x[i], array(call_ys[index][i]), COLORS[i])[0])
                global_ax_lines_put[index]['lines'].append(global_ax_lines_put[index]['ax'].plot(put_x[i], array(put_ys[index][i]), COLORS[i])[0])
        plt.draw()


def main():
    call_codes, put_codes, all_codes, dates = get_codes()
    dates_label = ',,'.join(dates).split(',')
    call_x, call_ys, put_x, put_ys = get_data(call_codes, put_codes, all_codes)
    xx, call_y2, put_y2 = fit(call_x, call_ys[-1], put_x, put_ys[-1])
    yy = list(range(len(call_y2)))
    x, y = meshgrid(xx, yy)
    fig = plt.figure(figsize=(12, 5.7))
    gs = gridspec.GridSpec(3, 6, figure=fig)
    ylabels = ['Delta', 'Gamma', 'Theta', 'Vega', 'Implied Volatility']
    call_gs = [gs[2:3, :1], gs[2:3, 1:2], gs[2:3, 2:3], gs[1:2, 2:3], gs[:1, 2:3]]
    put_gs = [gs[2:3, 3:4], gs[2:3, 4:5], gs[2:3, 5:6], gs[1:2, 5:6], gs[:1, 5:6]]
    # ---------------------------------------------------------------------------------------------------
    for index in range(5):
        call_ax = fig.add_subplot(call_gs[index])
        for i in yy:
            line, = call_ax.plot(call_x[i], call_ys[index][i], COLORS[i])
            global_ax_lines_call[index]['lines'].append(line)
        call_ax.set_xlabel('Strike Price')
        call_ax.set_ylabel(ylabels[index])
        call_ax.legend(dates, fontsize='xx-small')
        global_ax_lines_call[index]['ax'] = call_ax
        put_ax = fig.add_subplot(put_gs[index])
        for i in yy:
            line, = put_ax.plot(put_x[i], put_ys[index][i], COLORS[i])
            global_ax_lines_put[index]['lines'].append(line)
        put_ax.set_xlabel('Strike Price')
        put_ax.set_ylabel(ylabels[index])
        put_ax.legend(dates, fontsize='xx-small')
        global_ax_lines_put[index]['ax'] = put_ax
    ax_iv_sf_call = fig.add_subplot(gs[:2, :2], projection='3d')
    ax_iv_sf_call.view_init(ELEV, 0)
    surf_call = ax_iv_sf_call.plot_surface(x, y, array(call_y2), rstride=1, cstride=1, cmap='rainbow')
    ax_iv_sf_call.set_yticklabels(dates_label)
    ax_iv_sf_call.set_xlabel('Strike Price')
    ax_iv_sf_call.set_ylabel('Expiration Date')
    ax_iv_sf_call.set_zlabel('Implied Volatility')
    ax_iv_sf_call.set_title('Call Option')
    ax_iv_sf_put = fig.add_subplot(gs[:2, 3:5], projection='3d')
    ax_iv_sf_put.view_init(ELEV, 0)
    surf_put = ax_iv_sf_put.plot_surface(x, y, array(put_y2), rstride=1, cstride=1, cmap='rainbow')
    ax_iv_sf_put.set_yticklabels(dates_label)
    ax_iv_sf_put.set_xlabel('Strike Price')
    ax_iv_sf_put.set_ylabel('Expiration Date')
    ax_iv_sf_put.set_zlabel('Implied Volatility')
    ax_iv_sf_put.set_title('Put Option')
    plt.tight_layout()
    thread = Thread(target=update, args=(call_codes, put_codes, all_codes, x, y, yy, surf_call, surf_put, ax_iv_sf_call, ax_iv_sf_put))
    thread.setDaemon(True)
    thread.start()
    plt.show()


if __name__ == '__main__':
    main()
