#!/user/bin/env python
# -*-coding:utf-8-*-
import requests

if __name__ == '__main__':
    url = 'https://img1.baidu.com/it/u=4049022245,514596079&fm=253&fmt=auto&app=138&f=JPEG?w=889&h=500'
    #  .text(字符串、如html） .json()(application/json)  .content(二进制从content获取)
    img_data = requests.get(url=url).content

    with open('./tupian.jpg', 'wb') as fp:
        fp.write(img_data)
