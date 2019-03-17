"""
Author: shifulin
Email: shifulin666@qq.com
"""
# python3
from requests import get


def get_op_dates():
    url = "http://stock.finance.sina.com.cn/futures/api/openapi.php/StockOptionService.getStockName"
    dates = get(url).json()['result']['data']['contractMonth']
    return [''.join(i.split('-')) for i in dates][1:]


def get_op_expire_day(date):
    url = "http://stock.finance.sina.com.cn/futures/api/openapi.php/StockOptionService.getRemainderDay?date={date}01"
    data = get(url.format(date=date)).json()['result']['data']
    return data['expireDay'], int(data['remainderDays'])


def get_op_codes(date):
    url_up = "http://hq.sinajs.cn/list=OP_UP_510050" + str(date)[-4:]
    url_down = "http://hq.sinajs.cn/list=OP_DOWN_510050" + str(date)[-4:]
    data_up = str(get(url_up).content).replace('"', ',').split(',')
    codes_up = [i[7:] for i in data_up if i.startswith('CON_OP_')]
    data_down = str(get(url_down).content).replace('"', ',').split(',')
    codes_down = [i[7:] for i in data_down if i.startswith('CON_OP_')]
    return codes_up, codes_down


def get_op_price(code):
    url = "http://hq.sinajs.cn/list=CON_OP_{code}".format(code=code)
    data = get(url).content.decode('gbk')
    data = data[data.find('"') + 1: data.rfind('"')].split(',')
    fields = ['买量', '买价', '最新价', '卖价', '卖量', '持仓量', '涨幅', '行权价', '昨收价', '开盘价', '涨停价',
              '跌停价', '申卖价五', '申卖量五', '申卖价四', '申卖量四', '申卖价三', '申卖量三', '申卖价二',
              '申卖量二', '申卖价一', '申卖量一', '申买价一', '申买量一 ', '申买价二', '申买量二', '申买价三',
              '申买量三', '申买价四', '申买量四', '申买价五', '申买量五', '行情时间', '主力合约标识', '状态码',
              '标的证券类型', '标的股票', '期权合约简称', '振幅', '最高价', '最低价', '成交量', '成交额']
    result = list(zip(fields, data))
    return result


def get_50etf_price():
    url = "http://hq.sinajs.cn/list=sh510050"
    data = get(url).content.decode('gbk')
    data = data[data.find('"') + 1: data.rfind('"')].split(',')
    fields = ['股票名字', '今日开盘价', '昨日收盘价', '当前价格', '今日最高价', '今日最低价', '竞买价', '竞卖价',
              '成交的股票数', '成交金额', '买一量', '买一价', '买二量', '买二价', '买三量', '买三价', '买四量', '买四价',
              '买五量', '买五价', '卖一量', '卖一价', '卖二量', '卖二价', '卖三量', '卖三价', '卖四量', '卖四价',
              '卖五量', '卖五价', '日期', '时间']
    return list(zip(fields, data))


def get_op_greek_alphabet(code):
    url = "http://hq.sinajs.cn/list=CON_SO_{code}".format(code=code)
    data = get(url).content.decode('gbk')
    data = data[data.find('"') + 1: data.rfind('"')].split(',')
    fields = ['期权合约简称', '成交量', 'Delta', 'Gamma', 'Theta', 'Vega', '隐含波动率', '最高价', '最低价', '交易代码',
              '行权价', '最新价', '理论价值']
    return list(zip(fields, [data[0]] + data[4:]))


if __name__ == '__main__':
    dates = get_op_dates()
    print('期权合约月份：{}'.format(dates))
    for date in dates:
        print('期权月份{}：到期日{} 剩余天数{}'.format(date, *get_op_expire_day(date)))
    for date in dates:
        print('期权月份{}\n\t看涨期权代码：{}\n\t看跌期权代码：{}'.format(date, *get_op_codes(date)))
    for index, i in enumerate(get_op_price('10001585')):
        print('期权10001585', index, *i)
    for index, i in enumerate(get_50etf_price()):
        print('50ETF', index, *i)
    for index, i in enumerate(get_op_greek_alphabet('10001585')):
        print('期权10001585', index, *i)
