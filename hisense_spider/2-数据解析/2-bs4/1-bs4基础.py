#!/user/bin/env python
# -*-coding:utf-8-*-
from bs4 import BeautifulSoup

if __name__ == '__main__':
    # 将本地的html文档中的数据加载到该对象中
    fp  = open('./test.html', 'r', encoding='utf-8')
    soup = BeautifulSoup(fp, 'lxml')
    print(soup)