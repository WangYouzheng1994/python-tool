#!/user/bin/env python
# -*-coding:utf-8-*-
import logging
import time

import paramiko


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