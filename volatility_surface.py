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
global_lines = [[], [], [], []]


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
            up, down = [], []
            for date in dates:
                up_codes, down_codes = sina_op_api.get_op_codes(date)
                up.append(['CON_SO_' + i for i in up_codes])
                down.append(['CON_SO_' + i for i in down_codes])
            all_codes = ','.join([','.join(i) for i in up] + [','.join(i) for i in down])
            data = requests_get(all_codes)
            not_a_codes = [i[0][11:26] for i in data if not i[0].endswith('A')]  # 不考虑分红的
            for i in range(len(up)):
                up[i] = [j for j in up[i] if j in not_a_codes]
                down[i] = [j for j in down[i] if j in not_a_codes]
            break
        except (exceptions.ConnectionError, exceptions.ConnectTimeout) as e:
            print('连接出错，10秒后重试')
            print(e)
            sleep(10)
    return up, down, ','.join(not_a_codes), dates


def get_data(up, down, all_codes):
    x, y, vega = [], [], []
    for line in requests_get(all_codes):
        y.append(float(line[9]))
        vega.append(float(line[8]))
        x.append(float(line[13]))
    up_x, up_y, down_x, down_y, up_vega, down_vega = [], [], [], [], [], []
    b = 0
    for i in up:
        len_i = len(i)
        up_x.append(x[b:b + len_i])
        up_y.append(y[b:b + len_i])
        up_vega.append(vega[b:b + len_i])
        b += len_i
    for i in down:
        len_i = len(i)
        down_x.append(x[b:b + len_i])
        down_y.append(y[b:b + len_i])
        down_vega.append(vega[b:b + len_i])
        b += len_i
    return up_x, up_y, up_vega, down_x, down_y, down_vega


def fit(up_x, up_y, down_x, down_y):
    xx = set()
    for i in up_x:
        xx |= set(i)
    xx = sorted(xx)
    up_y2, down_y2 = [], []
    for i in range(len(up_x)):
        if xx == up_x[i]:
            up_y2.append(up_y[i])
        else:
            up_y2.append(polyval(polyfit(up_x[i], up_y[i], 2), xx))
        if xx == down_x[i]:
            down_y2.append(down_y[i])
        else:
            down_y2.append(polyval(polyfit(down_x[i], down_y[i], 2), xx))
    return xx, up_y2, down_y2


def update(up, down, all_codes, x, y, yy, surf1, ax1, surf2, ax2, axs):
    while True:
        sleep(3)  # 每隔3秒刷新一次
        up_x, up_y, up_vega, down_x, down_y, down_vega = get_data(up, down, all_codes)
        xx, up_y2, down_y2 = fit(up_x, up_y, down_x, down_y)
        surf1.remove()
        surf1 = ax1.plot_surface(x, y, array(up_y2) * 100.0, rstride=1, cstride=1, cmap='rainbow')
        surf2.remove()
        surf2 = ax2.plot_surface(x, y, array(down_y2) * 100.0, rstride=1, cstride=1, cmap='rainbow')
        for i in yy:
            axs[0].lines.remove(global_lines[0][i])
            axs[1].lines.remove(global_lines[1][i])
            axs[2].lines.remove(global_lines[2][i])
            axs[3].lines.remove(global_lines[3][i])
        for i in yy:
            global_lines[i] = []
        for i in yy:
            global_lines[0].append(axs[0].plot(up_x[i], array(up_y[i]) * 100.0, COLORS[i])[0])
            global_lines[1].append(axs[1].plot(down_x[i], array(up_vega[i]), COLORS[i])[0])
            global_lines[2].append(axs[2].plot(down_x[i], array(down_y[i]) * 100.0, COLORS[i])[0])
            global_lines[3].append(axs[3].plot(down_x[i], array(down_vega[i]), COLORS[i])[0])
        plt.draw()


def main():
    up, down, all_codes, dates = get_codes()
    dates_label = ',,'.join(dates).split(',')
    axs = []
    up_x, up_y, up_vega, down_x, down_y, down_vega = get_data(up, down, all_codes)
    xx, up_y2, down_y2 = fit(up_x, up_y, down_x, down_y)
    yy = list(range(len(up_y2)))
    x, y = meshgrid(xx, yy)
    fig = plt.figure(figsize=(13, 4.5))
    gs = gridspec.GridSpec(2, 6, figure=fig)
    ax1 = fig.add_subplot(gs[:, :2], projection='3d')
    surf1 = ax1.plot_surface(x, y, array(up_y2) * 100.0, rstride=1, cstride=1, cmap='rainbow')
    ax1.set_yticklabels(dates_label)
    ax1.set_xlabel('strike price')
    ax1.set_ylabel('expiration date')
    ax1.set_zlabel('implied volatility(%)')
    ax1.set_title('Call Option')
    ax = fig.add_subplot(gs[:1, 2:3])
    axs.append(ax)
    for i in yy:
        line, = ax.plot(up_x[i], array(up_y[i]) * 100.0, COLORS[i])
        global_lines[0].append(line)
    ax.set_xlabel('strike price')
    ax.set_ylabel('implied volatility(%)')
    ax.legend(dates, fontsize='xx-small')
    ax = fig.add_subplot(gs[1:2, 2:3])
    axs.append(ax)
    for i in yy:
        line, = ax.plot(up_x[i], up_vega[i], COLORS[i])
        global_lines[1].append(line)
    ax.set_xlabel('strike price')
    ax.set_ylabel('vega')
    ax.legend(dates, fontsize='xx-small')
    # ----------------------------------------------------------------------
    ax2 = fig.add_subplot(gs[:, 3:5], projection='3d')
    surf2 = ax2.plot_surface(x, y, array(down_y2) * 100.0, rstride=1, cstride=1, cmap='rainbow')
    ax2.set_yticklabels(dates_label)
    ax2.set_xlabel('strike price')
    ax2.set_ylabel('expiration date')
    ax2.set_zlabel('implied volatility(%)')
    ax2.set_title('Put Option')
    ax = fig.add_subplot(gs[:1, 5:6])
    axs.append(ax)
    for i in yy:
        line, = ax.plot(down_x[i], array(down_y[i]) * 100.0, COLORS[i])
        global_lines[2].append(line)
    ax.set_xlabel('strike price')
    ax.set_ylabel('implied volatility(%)')
    ax.legend(dates, fontsize='xx-small')
    ax = fig.add_subplot(gs[1:2, 5:6])
    axs.append(ax)
    for i in yy:
        line, = ax.plot(down_x[i], down_vega[i], COLORS[i])
        global_lines[3].append(line)
    ax.set_xlabel('strike price')
    ax.set_ylabel('vega')
    ax.legend(dates, fontsize='xx-small')
    plt.tight_layout()
    thread = Thread(target=update, args=(up, down, all_codes, x, y, yy, surf1, ax1, surf2, ax2, axs))
    thread.setDaemon(True)
    thread.start()
    plt.show()


if __name__ == '__main__':
    main()
