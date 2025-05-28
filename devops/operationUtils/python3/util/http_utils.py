#!/user/bin/env python
# -*-coding:utf-8-*-
import requests


class HttpUtils:
    @staticmethod
    def get(ip, port, uri, ishttps=False):
        protocol = 'http://'
        if (ishttps): protocol = 'https://'

        print(f'{protocol}' + ip + f'/{uri}')
        res = requests.get(f'{protocol}' + ip + f':{port}/{uri}')
        print(f'响应值{res}')
        return res

    @staticmethod
    def getUrl(url):
        protocol = 'http://'

        print(f'{url}')
        res = requests.get(f'{url}')
        print(f'响应值{res}')
        return res