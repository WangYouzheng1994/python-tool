#!/user/bin/env python
# -*-coding:utf-8-*-
from devops.operationUtils.python3.message.ding import DingdingGroupchat

# 发送钉钉
tongzhineirong="""
请周会前更新在项情况。
【金山文档 | WPS云文档】 JAVA类项目-人员分布表
https://www.kdocs.cn/l/cm12wKPDHFWZ
"""
# https://oapi.dingtalk.com/robot/send?access_token=cab3ca86afb841cbe419cab5301bed929d4eb3f12b7952a1d6bdcce2e81b1d20
access_token = 'cab3ca86afb841cbe419cab5301bed929d4eb3f12b7952a1d6bdcce2e81b1d20'
secret = 'SEC9679fe5beca635ec813fa519e6a73aa686e9fa3ed6e4612d6437743b7db5ee81'
dingding = DingdingGroupchat(access_token, secret)
dingding.send(f'通知内容：{tongzhineirong}', True)