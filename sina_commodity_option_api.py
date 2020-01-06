"""
Author: shifulin
Email: shifulin666@qq.com
"""
import json
import requests

PIN_ZHONG_PARAMS = {
    'io': {'product': 'io', 'exchange': 'cffex'},
    'm': {'product': 'm_o', 'exchange': 'dce'},
    'c': {'product': 'c_o', 'exchange': 'dce'},
    'i': {'product': 'i_o', 'exchange': 'dce'},
    'cf': {'product': 'cf', 'exchange': 'czce'},
    'sr': {'product': 'sr', 'exchange': 'czce'},
    'ta': {'product': 'ta', 'exchange': 'czce'},
    'ma': {'product': 'ma', 'exchange': 'czce'},
    'ru': {'product': 'ru_o', 'exchange': 'shfe'},
    'cu': {'product': 'cu_o', 'exchange': 'shfe'},
    'au': {'product': 'au_o', 'exchange': 'shfe'},
}
URL_T_QUOTATION = "http://stock.finance.sina.com.cn/futures/api/openapi.php/OptionService.getOptionData?" \
                  "type=futures&product={product}&exchange={exchange}&pinzhong={code}"
URL_KLINE = "https://stock.finance.sina.com.cn/futures/api/jsonp.php//" \
            "FutureOptionAllService.getOptionDayline?symbol={code}"
URL_PRICE = "https://hq.sinajs.cn/etag.php?list=P_OP_{code}"
URL_UNDERLYING_PRICE = "http://hq.sinajs.cn/list={code}"
URL_000300 = "http://hq.sinajs.cn/list=sh000300"


def get_t_quotation(code):
    """获取T型报价数据"""
    p = ''.join(filter(str.isalpha, code))
    data = requests.get(URL_T_QUOTATION.format(code=code, **PIN_ZHONG_PARAMS[p])).json()['result']['data']
    up, down = data['up'], data['down']
    for i in down:
        s = []
        for j in i[-1][::-1]:
            if j.isdigit():
                s.append(j)
            else:
                break
        strike_price = ''.join(s[::-1])
        i.insert(-1, strike_price)
    return up, down


def get_option_kline(code):
    """获取日K线数据"""
    return json.loads(requests.get(URL_KLINE.format(code=code)).content.split(b'(')[1].split(b')')[0])


def get_option_price(code):
    """获取实时行情数据"""
    data = requests.get(URL_PRICE.format(code=code)).content.split(b'"')[1].decode().split(',')
    return data


def get_underlying_price(code):
    """获取标的(期货)实时行情"""
    return requests.get(URL_UNDERLYING_PRICE.format(code=code)).content.split(b'"')[1].decode('gbk').split(',')


def get_000300_price():
    """获取指数000300实时行情"""
    return requests.get(URL_000300).content.split(b'"')[1].decode('gbk').split(',')


def my_test():
    header = ['买量', '买价', '最新价', '卖价', '卖量', '持仓量', '涨跌(%)', '行权价', '代码']
    up, down = get_t_quotation('io2002')
    for i in up + down:
        print(list(zip(header, i)))
    day_kline = get_option_kline('m2005C2400')
    print()
    for i in day_kline:
        print('日期:{d}, 开:{o}, 高:{h}, 低:{l}, 收:{c}, 成交:{v}'.format(**i))
    header2 = ['买量', '买价', '最新价', '卖价', '卖量', '持仓量', '涨幅', '行权价', '昨收价', '开盘价', '涨停价',
               '跌停价', '申卖价五', '申卖量五', '申卖价四', '申卖量四', '申卖价三', '申卖量三', '申卖价二',
               '申卖量二', '申卖价一', '申卖量一', '申买价一', '申买量一', '申买价二', '申买量二', '申买价三',
               '申买量三', '申买价四', '申买量四', '申买价五', '申买量五', '行情时间', '主力合约标识', '状态码',
               '标的证券类型', '标的股票', '期权合约简称', '振幅', '最高价', '最低价', '成交量', '成交额']
    price_data = get_option_price('io2002C4000')
    print()
    for i in zip(header2, price_data):
        print(i)
    header3 = ['期货名称', '现在交易时间', '开盘价', '最高价', '最低价', '(昨?)收盘价', '竞买价', '竞卖价', '最新价',
               '动态结算价', '昨日结算价', '买量', '卖量', '持仓量', '成交量', '交易所', '品种', '日期', '是否热门',
               '5天最高', '5天最低', '10天最高', '10天最低', '20天最高', '20天最低', '55天最高', '55天最低', '加权平均']
    future_data = get_underlying_price('M2005')
    print()
    for i in zip(header3, future_data):
        print(i)
    header4 = ['股票名字', '今日开盘价', '昨日收盘价', '当前价格', '今日最高价', '今日最低价', '竞买价', '竞卖价',
               '成交的股票数', '成交金额', '买一量', '买一价', '买二量', '买二价', '买三量', '买三价', '买四量', '买四价',
               '买五量', '买五价', '卖一量', '卖一价', '卖二量', '卖二价', '卖三量', '卖三价', '卖四量', '卖四价',
               '卖五量', '卖五价', '日期', '时间']
    price_000300 = get_000300_price()
    print()
    for i in zip(header4, price_000300):
        print(i)


if __name__ == '__main__':
    my_test()


