#!/usr/bin/env python
# -*- coding:utf-8 -*-
# 简单爬取
import requests
if __name__ == "__main__":
    url = 'https://www.sogou.com/'
    res = requests.get(url)
    page_text = res.text
    print(page_text)
    with open('../sougou.html', 'w', encoding='utf-8') as fp:
        fp.write(page_text)
    print('爬取搜狗结束~')