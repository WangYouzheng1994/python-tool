#!/user/bin/env python
# -*-coding:utf-8-*-
import requests
import json
if __name__ == '__main__':
    # 设置请求路径
    post_url = 'https://fanyi.baidu.com/sug'
    # 设置请求头
    # 设置UA
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
    }
    # 设置请求参数
    word = input('请输入要翻译的英文：')
    data = {
        'kw': word
    }
    # 发送post请求
    response = requests.post(url=post_url, data=data, headers=headers)
    # 获取结果
    # 如果确认响应值是json 才可以用 json()
    dic_obj = response.json()
    # 存储结果集
    fileName = word+'.json'
    fp = open(fileName, 'w', encoding='utf-8')
    json.dump(dic_obj, fp=fp, ensure_ascii=False)

    print('over!')