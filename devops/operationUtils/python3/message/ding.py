#!/user/bin/env python
# -*-coding:utf-8-*-
import logging
import time
import hmac
import hashlib
import base64
import urllib.parse
import requests
import json


class DingdingGroupchat:

    def __init__(self, access_token, secret):
        if not (access_token and secret):
            logging.error("参数为空！access_token=%s, secret=%s", access_token, secret)
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
            logging.exception(f"请求发生错误: {e}")
        except Exception as e:
            logging.exception(f"发生未知错误: {e}")
