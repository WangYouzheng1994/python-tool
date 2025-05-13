#!/user/bin/env python
# -*- coding:utf-8 -*-
import requests
if __name__ == '__main__':
    # UA伪装
    headers = {
        'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
    }
    url = 'https://www.sogou.com/web'
    kw = input('enter a word:')
    param = {
        'query': kw
    }
    # get请求
    page_text = requests.get(url=url, params=param, headers=headers).text

    with open('../sougou_list.html', 'w', encoding='utf-8') as fp:
        fp.write(page_text)
    print('爬取搜狗结束~')
