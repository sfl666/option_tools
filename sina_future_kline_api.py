"""
Author: shifulin
Email: shifulin666@qq.com
"""
import json
import requests


URL_KLINE = "https://stock2.finance.sina.com.cn/futures/api/jsonp.php//" \
            "InnerFuturesNewService.getDailyKLine?symbol={code}"


def get_future_day_kline(code):
    # 日期, 开, 高, 低, 收, 成交量, 持仓量
    data = requests.get(URL_KLINE.format(code=code)).content
    kline = json.loads(data[data.find(b'(') + 1: data.rfind(b')')])
    # for i in kline:
    #     print(i)
    # print(type(kline[0]['o']))
    return kline


if __name__ == '__main__':
    get_future_day_kline('M2005')

