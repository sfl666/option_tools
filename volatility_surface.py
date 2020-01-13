"""
Author: shifulin
Email: shifulin666@qq.com
"""
# python3

from time import sleep
from threading import Thread, Lock

from requests import get, exceptions
from numpy import polyfit, polyval, meshgrid, array, nan
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from mpl_toolkits.mplot3d import Axes3D

import sina_etf_option_api

COLORS = ['blue', 'yellow', 'lime', 'red', 'purple', 'slategray', 'tomato', 'orange', 'darkred', 'aqua']
global_ax_lines_call = [{'ax': None, 'lines': []} for _ in range(5)]
global_ax_lines_put = [{'ax': None, 'lines': []} for _ in range(5)]
update_picture_lock = Lock()
ELEV = 30
AZIM = 120


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


def get_codes(cate, exchange, underlying, dividend):
    while True:
        try:
            dates = sorted(sina_etf_option_api.get_option_dates(cate=cate, exchange=exchange))
            call, put = [], []
            for date in dates:
                call_codes, put_codes = sina_etf_option_api.get_option_codes(date, underlying=underlying)
                call.append(['CON_SO_' + i for i in call_codes])
                put.append(['CON_SO_' + i for i in put_codes])
            all_codes = ','.join([','.join(i) for i in call] + [','.join(i) for i in put])
            data = requests_get(all_codes)
            if dividend:
                codes_tmp = [i[0][11:26] for i in data]  # 考虑分红
            else:
                codes_tmp = [i[0][11:26] for i in data if not i[0].endswith('A')]  # 不考虑分红
            for i in range(len(call)):
                call[i] = [j for j in call[i] if j in codes_tmp]
                put[i] = [j for j in put[i] if j in codes_tmp]
            break
        except (exceptions.ConnectionError, exceptions.ConnectTimeout) as e:
            print('连接出错，10秒后重试')
            print(e)
            sleep(10)
    return call, put, ','.join(codes_tmp), dates


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


def knockout_small_value(x, y):
    length = len(x)
    new_x = [x[i] for i in range(length) if y[i] > 0.01]
    new_y = [i for i in y if i > 0.01]
    return new_x, new_y


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
            new_x, new_y = knockout_small_value(call_x[i], call_y[i])
            tmp = polyval(polyfit(new_x, new_y, 2), xx)
            tmp[tmp < 0.0] = 0.0
            tmp_y, index_y = [], 0
            for index, j in enumerate(xx):
                if j in call_x[i]:
                    tmp_y.append(call_y[i][index_y])
                    index_y += 1
                else:
                    tmp_y.append(tmp[index])
            call_y2.append(tmp_y)
        if xx == put_x[i]:
            put_y2.append(put_y[i])
        else:
            new_x, new_y = knockout_small_value(put_x[i], put_y[i])
            tmp = polyval(polyfit(new_x, new_y, 2), xx)
            tmp[tmp < 0.0] = 0.0
            tmp_y, index_y = [], 0
            for index, j in enumerate(xx):
                if j in put_x[i]:
                    tmp_y.append(put_y[i][index_y])
                    index_y += 1
                else:
                    tmp_y.append(tmp[index])
            put_y2.append(tmp_y)
    return xx, call_y2, put_y2


def not_fit(call_x, call_y, put_x, put_y):
    xx = set()
    for i in call_x:
        xx |= set(i)
    xx = sorted(xx)
    call_y2, put_y2 = [], []
    for i in range(len(call_x)):
        if xx == call_x[i]:
            call_y2.append(call_y[i])
        else:
            tmp_y, index_y = [], 0
            for index, j in enumerate(xx):
                if j in call_x[i]:
                    tmp_y.append(call_y[i][index_y])
                    index_y += 1
                else:
                    tmp_y.append(nan)
            call_y2.append(tmp_y)
        if xx == put_x[i]:
            put_y2.append(put_y[i])
        else:
            tmp_y, index_y = [], 0
            for index, j in enumerate(xx):
                if j in put_x[i]:
                    tmp_y.append(put_y[i][index_y])
                    index_y += 1
                else:
                    tmp_y.append(nan)
            put_y2.append(tmp_y)
    return xx, call_y2, put_y2


def update(call_codes, put_codes, all_codes, x, y, yy, surf_call, surf_put, ax_iv_sf_call, ax_iv_sf_put, is_fit):
    azim = AZIM
    while True:
        # sleep(5)  # 每隔5秒刷新一次
        sleep(10)
        with update_picture_lock:
            call_x, call_ys, put_x, put_ys = get_data(call_codes, put_codes, all_codes)
            if is_fit:
                xx, call_y2, put_y2 = fit(call_x, call_ys[-1], put_x, put_ys[-1])
            else:
                xx, call_y2, put_y2 = not_fit(call_x, call_ys[-1], put_x, put_ys[-1])
            surf_call.remove()
            azim += 15
            if azim > 360:
                azim -= 360
            ax_iv_sf_call.view_init(ELEV, azim)
            # surf_call = ax_iv_sf_call.plot_surface(x, y, array(call_y2), rstride=1, cstride=1, cmap='rainbow')
            surf_call = ax_iv_sf_call.plot_wireframe(x, y, array(call_y2), rstride=1, cstride=1)
            surf_put.remove()
            ax_iv_sf_put.view_init(ELEV, azim)
            # surf_put = ax_iv_sf_put.plot_surface(x, y, array(put_y2), rstride=1, cstride=1, cmap='rainbow')
            surf_put = ax_iv_sf_put.plot_wireframe(x, y, array(put_y2), rstride=1, cstride=1)
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


def main(cate, exchange, underlying, dividend=True, is_fit=True):
    call_codes, put_codes, all_codes, dates = get_codes(cate, exchange, underlying, dividend)
    dates_label = ',,'.join(dates).split(',')
    call_x, call_ys, put_x, put_ys = get_data(call_codes, put_codes, all_codes)
    if is_fit:
        xx, call_y2, put_y2 = fit(call_x, call_ys[-1], put_x, put_ys[-1])
    else:
        xx, call_y2, put_y2 = not_fit(call_x, call_ys[-1], put_x, put_ys[-1])
    yy = list(range(len(call_y2)))
    x, y = meshgrid(xx, yy)
    fig = plt.figure(figsize=(12, 5.7))
    fig.canvas.mpl_connect('button_press_event', lambda event: update_picture_lock.acquire())
    fig.canvas.mpl_connect('button_release_event', lambda event: update_picture_lock.release())
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
    ax_iv_sf_call.view_init(ELEV, AZIM)
    # surf_call = ax_iv_sf_call.plot_surface(x, y, array(call_y2), rstride=1, cstride=1, cmap='rainbow')
    surf_call = ax_iv_sf_call.plot_wireframe(x, y, array(call_y2), rstride=1, cstride=1, cmap='rainbow')
    ax_iv_sf_call.set_yticklabels(dates_label)
    ax_iv_sf_call.set_xlabel('Strike Price')
    ax_iv_sf_call.set_ylabel('Expiration Date')
    ax_iv_sf_call.set_zlabel('Implied Volatility')
    ax_iv_sf_call.set_title('Call Option')
    ax_iv_sf_put = fig.add_subplot(gs[:2, 3:5], projection='3d')
    ax_iv_sf_put.view_init(ELEV, AZIM)
    # surf_put = ax_iv_sf_put.plot_surface(x, y, array(put_y2), rstride=1, cstride=1, cmap='rainbow')
    surf_put = ax_iv_sf_put.plot_wireframe(x, y, array(put_y2), rstride=1, cstride=1, cmap='rainbow')
    ax_iv_sf_put.set_yticklabels(dates_label)
    ax_iv_sf_put.set_xlabel('Strike Price')
    ax_iv_sf_put.set_ylabel('Expiration Date')
    ax_iv_sf_put.set_zlabel('Implied Volatility')
    ax_iv_sf_put.set_title('Put Option')
    plt.tight_layout()
    thread = Thread(target=update, args=(call_codes, put_codes, all_codes, x, y, yy, surf_call, surf_put, ax_iv_sf_call, ax_iv_sf_put, is_fit))
    thread.setDaemon(True)
    thread.start()
    plt.show()


if __name__ == '__main__':
    category = '50ETF'
    underlying_security = '510050'
    # category = '300ETF'
    # underlying_security = '510300'
    main(cate=category, exchange='null', underlying=underlying_security, dividend=False, is_fit=True)
