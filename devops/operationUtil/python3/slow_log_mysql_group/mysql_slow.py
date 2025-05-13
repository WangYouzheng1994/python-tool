#!/user/bin/env python
# -*-coding:utf-8-*-
# raise_tech

import sys
import re
import time
import os
import subprocess

from slow_mysql_groupchat_robot import DingdingGroupchat

#
BasePath = os.getcwd()
# 获取输入的日志文件
if len(sys.argv) < 2:
    print("请输入文件名：Usage: " + sys.argv[0] + " filename")
    sys.exit(1)
logfile = sys.argv[1]
status, ip = subprocess.getstatusoutput(
    "ip a|grep -w inet|egrep -v 'vir|127.0.0.1'|awk -F'[ /]+' '{print $3}'| xargs |sed 's/ /:/g'")

if status != 0:
    ip = '---'
messege = {'localdb': '本地测试数据库'}
default_messege = '---'
db = '---'
print(f'测试：{messege}')

fd = open(logfile, "r")
fd.seek(0, 2)
ret = 0
sql = ''
line_new = []

secret = 'SEC6d00bdfed15181ef1c93c6f4527893269656847cd55f248cefc6a4d3b327b1ce'  # opsyndex
access_token = '508dc9040f4660229b6ae96eb02c64c3cebba080518be08db481fc3f931467f4'
dingding = DingdingGroupchat(access_token, secret)
while 1:
    line = fd.readline()
    if line:
        if ret == 0:
            if line.startswith("# Query_time:"):
                use_time = line.split()[2]
                continue
            if line.startswith('use '):
                db = line.split()[1].split(';')[0]
                try:
                    default_messege = messege[db]
                except Exception:
                    pass
            if line.startswith('SET timestamp'):
                ret = 1
                # print use_time,db,sql
        elif ret == 1:
            if line.startswith('# Time:') or line.startswith('# User@Host:'):
                sql = ' '.join(line_new)
                if sql != '':
                    if "SQL_NO_CACHE" in sql:
                        sql = re.sub('\/\*!40001 SQL_NO_CACHE \*\/', '', sql)
                    # sql = re.sub('\`', '\\`', sql)
                    # sql = re.sub('\(', '\\(', sql)
                    # sql = re.sub('\)', '\\)', sql)
                    # sql = re.sub('\*', '\\*', sql)
                    # sql = re.sub('\>', '\\>', sql)
                    # sql = re.sub('\<', '\\<', sql)
                    Msg = ("报警:"
                           "#主机:%s"
                           "#触发原因:%s数据库出现慢查询#慢查询时间:%s秒"
                           "#影响范围:%s"
                           "#慢查询语句:%s#") % (
                    ip, db, use_time, default_messege, sql)
                    os.system('python  %s/sent_weixin.py %s' %(BasePath,Msg))
                    # 发送钉钉群聊
                    # dingding.send(Msg)
                    line_new = []
                    sql = ''
                    ret = 0
            else:

                line_new.append(line.strip())
        else:
            pass
    else:
        sql = ' '.join(line_new)
        if sql != '':
            if "SQL_NO_CACHE" in sql:
                sql = re.sub('\/\*!40001 SQL_NO_CACHE \*\/', '', sql)
            # sql = re.sub('\`', '\\`', sql)
            # sql = re.sub('\(', '\\(', sql)
            # sql = re.sub('\)', '\\)', sql)
            # sql = re.sub('\*', '\\*', sql)
            # sql = re.sub('\>', '\\>', sql)
            # sql = re.sub('\<', '\\<', sql)
            Msg = "报警:#主机:%s#触发原因:%s数据库出现慢查询#慢查询时间:%s秒#影响范围:%s#慢查询语句:%s#" % (
            ip, db, use_time, default_messege, sql)
            print('开始发送信息')
            os.system('python  %s/sent_weixin.py %s' %(BasePath,Msg))
            # 发送钉钉群聊
            # dingding.send(Msg)
            line_new = []
            sql = ''
            ret = 0
        else:
            print('没扫到，睡眠~')
            time.sleep(3)
fd.close()
print("执行结束")
