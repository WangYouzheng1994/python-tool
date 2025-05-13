#!/user/bin/env python
# -*-coding:utf-8-*-
from bs4 import BeautifulSoup
if __name__ == '__main__':
    fp = open('./test.html', 'r', encoding='utf-8')
    soup = BeautifulSoup(fp, 'lxml')
    # soup.tagName 返回的是html中第一次出现的tagName标签
    print(soup.a)
    print(soup.find('div', class_ = 'abc_div'))
    print(soup.find_all('div'))