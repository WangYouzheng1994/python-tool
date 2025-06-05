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
        logging.info("正在连接服务器")
        self._ssh_fd.connect(hostname, username=username, password=password, port=port)

        self._transport = paramiko.Transport((hostname, port))
        self._transport.connect(username=username, password=password)
        # 创建sftp客户端
        self.sftp = paramiko.SFTPClient.from_transport(self._transport)
        logging.info("连接成功")

        # 尝试 Windows 命令
        stdin, stdout, stderr = self._ssh_fd.exec_command("echo %OS%")
        output = stdout.read().decode()
        if "Windows_NT" in output:
            self.os_name = "windows"

        # 尝试 Linux 命令
        stdin, stdout, stderr = self._ssh_fd.exec_command("uname -s")
        output = stdout.read().decode()
        if "Linux" in output:
            self.os_name = "linux"

        # 尝试 macOS 命令
        stdin, stdout, stderr = self._ssh_fd.exec_command("sw_vers")
        output = stdout.read().decode()
        if "ProductName" in output:
            self.os_name = "macos"

    def close_cont(self):
        self._ssh_fd.close()
        self.sftp.close()
        logging.info('关闭连接')

    """
    获取文件分隔符
    """

    def get_directory_separator(self):
        directory_separator = "/"
        if self.os_name == 'windows':  # windows
            directory_separator = "\\"
        else:  # linux/unix
            directory_separator = "/"

        return directory_separator

    """
    上传文件到Linux远程服务器
    local_src： 本地文件路径包含文件
    remote_src： 服务器上保存文件的路径，不包含文件就是目录 
    """

    def copy_file(self, local_src, remote_src, file_name):
        try:
            self.sftp.remove(remote_src + self.get_directory_separator() + file_name)
        except Exception as e:
            logging.exception("刪除报错了")
        logging.info("正在上传文件，请等待........")
        self.sftp.put(local_src, remote_src + self.get_directory_separator() + file_name)
        logging.info("文件上传成功...............")
        return True

    """
    执行Linux命令
    cmd: Linux命令 例: ls /
    path: 默认为空，如果不为空，需要切换目录
    """

    def exec_cmd(self, cmd, path=None):
        path = f"cd {path} &&" if path else ""
        if path:
            logging.info("执行命令前，进行路径跳转：%s", path)
            # self._ssh_fd.exec_command(f"cd {path}", get_pty=True)

        logging.info("执行远程命令：%s", cmd)
        stdin, stdout, stderr = self._ssh_fd.exec_command(path + cmd, get_pty=False)
        out_res = ''
        err_res = ''
        if stdout.channel.recv_exit_status() != 0:
            for line in stdout.readlines():
                logging.info(line)
                out_res += line
        else:
            for line in stderr.readlines():
                logging.info(line)
                err_res += line
        exit_status = stdout.channel.recv_exit_status()

        # if stdout.channel.recv_exit_status() != 0:
        #     for line in stderr.readlines():
        #         logging.info(line)
        #         res += line
        #     return False, res
        # else:
        #     for line in stdout.readlines():
        #         logging.info(line)
        #         res += line
        #     return True, res
        logging.info("命令执行结果，out:%s, err:%s, exit_status: %s", out_res, err_res, exit_status)
        return (exit_status == 0, out_res, err_res)

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
