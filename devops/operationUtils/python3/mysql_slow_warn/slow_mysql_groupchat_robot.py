#!/user/bin/env python
# -*-coding:utf-8-*-
# 蒙牛正式环境慢sql机器人
import time
import hmac
import hashlib
import base64
import urllib.parse
import requests
import json

class DingdingGroupchat:
    def __init__(self, access_token, secret):
        self.access_token = access_token
        self.secret = secret
        self.url = f'https://oapi.dingtalk.com/robot/send?access_token={self.access_token}'

    def send(self, content, is_at_all=False):
        try:
            timestamp = str(round(time.time() * 1000))
            secret_enc = self.secret.encode('utf-8')
            string_to_sign = '{}\n{}'.format(timestamp, self.secret)
            string_to_sign_enc = string_to_sign.encode('utf-8')
            hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
            sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))

            data = {
                "msgtype": "text",
                "text": {
                    "content": content
                },
                "at": {
                    "isAtAll": is_at_all
                }
            }
            headers = {'Content-Type': 'application/json;charset=utf-8'}
            full_url = self.url + '&timestamp=' + timestamp + '&sign=' + sign
            r = requests.post(full_url, headers=headers, data=json.dumps(data))
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            print(f"请求发生错误: {e}")
        except Exception as e:
            print(f"发生未知错误: {e}")


if __name__ == '__main__':
    # MN群
    access_token = 'a6c6f183c0b4f411028f828728cc731d811d5d1c3e50066597d50b0a90ce6d79'
    secret = 'SECb0134d59803807164943ddd032314040d8588ff15635c7409a4bc899e1a45718'
    dingding = DingdingGroupchat(access_token, secret)
    result = dingding.send("您有一条新工单~请及时处理~~(*￣︶￣) 啦啦啦啦啦啦啦啦", is_at_all=False)
    print('钉钉消息发送结果：', result)