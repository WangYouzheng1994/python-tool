#!/user/bin/env python
# -*-coding:utf-8-*-
import requests
import json
if __name__ == '__main__':
    # 指定url
    get_url = 'https://movie.douban.com/j/chart/top_list'
    # ua伪装
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
    }
    # 请求参数
    param = {
        'type': '5',
        'interval_id': '100:90',
        'action': '',
        'start': '0',
        'limit': '20'
    }

    # get请求
    page_text = requests.get(url=get_url, params=param, headers=headers)
    res_json = page_text.json()

    fp = open('../db_movie.json', 'w', encoding='utf-8')
    json.dump(res_json, fp=fp, ensure_ascii=False)

    print('获取结束！')