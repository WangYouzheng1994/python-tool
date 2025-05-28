#!/user/bin/env python
# -*-coding:utf-8-*-
import paramiko
import time
import os
import logging
import requests

from devops.operationUtils.python3.util.http_utils import HttpUtils


class contnet_shell:
    """
        构造函数：创建对象时执行
        hostname：IP地址
        username：用户名
        password：密码
    """

    def __init__(self, hostname, username, password, port=22):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.port = port
        self._ssh_fd = paramiko.SSHClient()
        self._ssh_fd.set_missing_host_key_policy(paramiko.AutoAddPolicy)
        logging.info("正在连接linux服务器")
        self._ssh_fd.connect(hostname, username=username, password=password, port=port)

        self._transport = paramiko.Transport((hostname, port))
        self._transport.connect(username=username, password=password)
        # 创建sftp客户端
        self.sftp = paramiko.SFTPClient.from_transport(self._transport)
        logging.info("连接Linux成功")

    def close_cont(self):
        self._ssh_fd.close()
        self.sftp.close()
        print('关闭连接')

    """
    上传文件到Linux远程服务器
    local_src： 本地文件路径 
    remote_src： 服务器上保存文件的路径 
    """

    def copy_file(self, local_src, remote_src):
        logging.info("正在上传文件，请等待........")
        self.sftp.put(local_src, remote_src)
        logging.info("文件上传成功...............")

    """
    执行Linux命令
    cmd: Linux命令 例: ls /
    """

    def exec_cmd(self, cmd):
        stdin, stdout, stderr = self._ssh_fd.exec_command(cmd)
        res = ''
        if stdout.channel.recv_exit_status() != 0:
            for line in stderr.readlines():
                logging.info(line)
                res += line
            return False, res
        else:
            for line in stdout.readlines():
                logging.info(line)
                res += line
            return True, res

    def yum(self, cmd):
        cmd = cmd + '\n'  # 加一个回车键
        invoke = self._ssh_fd.invoke_shell()
        invoke.send(cmd)
        res_str = ''

        while True:
            time.sleep(0.5)
            res = invoke.recv(65535).decode("utf-8")
            logging.info(res)
            res_str += res
            lines = res.split('\n')
            last_line = lines[len(lines) - 1]

            if last_line.strip().count('[y/d/N]') > 0 or last_line.strip().count(r'[y/N]'):
                invoke.send('y' + '\n')
            elif last_line.count('[' + self.username + '@') > 0:
                break
        return res_str

ip='192.168.0.71'
user='root'
pwd=('wyz123!@#')

# 远程登录
logging.basicConfig(level=logging.INFO)
shell = contnet_shell(ip,user,pwd)

# 若服务器没有docker 安装docker -- START
# is_exists, res = shell.exec_cmd('docker -v')
# if not is_exists:
#     shell.yum('yum install -y docker')
# shell.exec_cmd('systemctl stop firewalld')  # 关闭防火墙
# 若服务器没有docker 安装docker -- END

# 克隆项目到本地，然后打包上传至服务器
# if not os.path.exists('./java_demo'):
#     os.system('git clone https://gitee.com/aurora_f/java_demo')
# os.chdir(os.getcwd() + '\\java_demo\\')
# os.system('git pull')  # 拉取最新的代码到本地
# os.system('mvn install')
# shell.copy_file('./target/myDemo.jar', '/opt/myDemo.jar')

# 向地址发送请求，通过状态码判断是否成功
# time.sleep(5)
res = ""
ip='localhost'
port='9200'
uri='/test/isOk'


try:
    res = HttpUtils.get(ip, port, uri)
except Exception as e:
    raise e
if (res.status_code == 200):
    print('成功！！！\n')
else:
    print(f'返回值：{res.status_code}, 容器启动不成功\n')
shell.close_cont()
