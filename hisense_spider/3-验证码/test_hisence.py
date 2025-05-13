#!/user/bin/env python
# -*-coding:utf-8-*-

import requests
import base64
from PIL import Image
from io import BytesIO
import ddddocr

if __name__ == '__main__':
    ocr = ddddocr.DdddOcr()
    # 获取验证码url
    url = 'https://hcrmportal.hisense.com/api/captcha'
    # UA伪装
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
    }

    # 循环抓取海信的验证码50个
    for i in range(50):
        res = requests.get(url)

        my_string = ''.join( res.json()['Data'])
        image_data = base64.b64decode(my_string)

        res = ocr.classification(image_data)
        print(f'验证码解析为：{res}')

    # 模拟登陆海信心连心
