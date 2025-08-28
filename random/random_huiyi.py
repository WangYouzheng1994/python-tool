#!/user/bin/env python
# -*-coding:utf-8-*-

import random

# from devops.operationUtils.python3.mysql.slow_mysql_groupchat_robot import DingdingGroupchat
from devops.operationUtils.python3.message.ding import DingdingGroupchat
# 示例集合（可以是任何可迭代对象）
sample_set = names = {
    "唐宇", "赵树全", "石磊", "卢帅", "乔通",
    "刘宝航", "刘宇航", "刁沛森", "冯俊杰", "江春阳",
     "李兆旭", "黄绪鹏", "刘卫航", "朱涛", "刘新荣", "王志通", "杜家晖"
}


def randomize_collection(collection):
    """
    接收一个集合，返回其元素的随机排列列表

    参数:
        collection: 可迭代对象，如列表、集合等

    返回:
        list: 随机排列后的列表
    """
    # 转换为列表以便打乱顺序
    elements = list(collection)
    # 使用 Fisher-Yates 洗牌算法打乱顺序
    random.shuffle(elements)
    return elements


# 生成随机排列
randomized_list = randomize_collection(sample_set)

print("原始集合:", sample_set)
print("随机排列:", randomized_list)

# 发送钉钉

# https://oapi.dingtalk.com/robot/send?access_token=cab3ca86afb841cbe419cab5301bed929d4eb3f12b7952a1d6bdcce2e81b1d20
access_token = 'cab3ca86afb841cbe419cab5301bed929d4eb3f12b7952a1d6bdcce2e81b1d20'
secret = 'SEC9679fe5beca635ec813fa519e6a73aa686e9fa3ed6e4612d6437743b7db5ee81'
dingding = DingdingGroupchat(access_token, secret)
dingding.send(f'本周会议顺序：{randomized_list}', True)
