"""
Author: shifulin
Email: shifulin666@qq.com
"""
import requests


URL = "https://stock.finance.sina.com.cn/futures/view/optionsDP.php/{product}/{exchange}"


def get_instruments(product, exchange):
    data = requests.get(URL.format(product=product, exchange=exchange)).content
    data1 = data[data.find(b'option_suffix'):]
    data2 = data1[:data1.find(b'</ul>')].split(b'</li>')
    instruments = sorted(set(i[i.rfind(b'>') + 1:].decode().lower() for i in data2[:-1]), key=lambda x: int(x[-4:]))
    return instruments


if __name__ == '__main__':
    print(get_instruments('ma', 'czce'))

