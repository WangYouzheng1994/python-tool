#!/user/bin/env python
# -*-coding:utf-8-*-
# 给钉钉群聊机器人发消息

import time
import hmac
import hashlib
import base64
import urllib.parse
import requests
import json


if __name__ == '__main__':
    # 接口地址
    url='https://oapi.dingtalk.com/robot/send?access_token=6acffc579b634daed25912d3abc98635762743ab875eeacd3f94e8fd68276cc6'
    timestamp = str(round(time.time() * 1000))
    secret = 'SECf0f76348741fe7356b19daf0dc0ead101fd7077a30c748585e35aa7c94cf3dce'
    secret_enc = secret.encode('utf-8')
    string_to_sign = '{}\n{}'.format(timestamp, secret)
    string_to_sign_enc = string_to_sign.encode('utf-8')
    hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
    sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
    print(timestamp)
    print(sign)

    # 要发送的消息内容
    data = {
        "msgtype": "text",
        "text": {
            "content": "您有一条新工单~请及时处理~~(*￣︶￣)"
        },
        "at": {
            "isAtAll": False
        }
    }
    headers = {'Content-Type': 'application/json;charset=utf-8'}
    url = url + '&timestamp='+timestamp + '&sign=' + sign
    # 发送POST请求，将消息内容转换为json格式
    r = requests.post(url, headers=headers, data=json.dumps(data))
    print('钉钉消息发送结果：', r.json())