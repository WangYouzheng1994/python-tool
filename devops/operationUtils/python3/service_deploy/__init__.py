#!/user/bin/env python
# -*-coding:utf-8-*-
import logging
import os
import sys

from devops.operationUtils.python3.service_deploy.git_utils import GitUtils
from devops.operationUtils.python3.service_deploy.shell_utils import contnet_shell
from devops.operationUtils.python3.util.http_utils import HttpUtils
from devops.operationUtils.python3.util.mysql_pool_utils import MySQLHelper
from devops.operationUtils.python3.util.yaml_utils import YamlUtils

# https://blog.csdn.net/weixin_45286211/article/details/119338305

logging.basicConfig(level=logging.INFO)

# 访问特定参数（配置文件）用于构建不同的项目。
config_name = 'config'
if len(sys.argv) > 1:
    config_name = sys.argv[1]
# 获取当前工作目录的绝对路径
current_working_directory = os.getcwd()
# 构建相对路径的绝对路径读取配置文件目录的yaml配置
config_absolute_path = os.path.abspath(os.path.join(current_working_directory, 'config', f'{config_name}.yaml'))
yaml = YamlUtils(config_absolute_path)


def run():
    """
    1.clone项目
    2.按照deploy构建。
    3.获取对应的部署清单(mysql)
    4.推送，并启动，测试，发送消息。
    """

    # 1. 加载yaml，

    deploy = yaml.query("deploy")
    if not deploy.deploy_names:
        print("你需要在config.yaml中填入deploy_names:发布列表")
    else:
        print(f"读取到deploy配置：{deploy.deploy_names}，开始构建")

    getProjectInfo()

def getProjectInfo(service_name):
    db_map = yaml.query_and_map("base.config.db")
    # 读取mysql对应的项目配置
    dbinfo = MySQLHelper(host=db_map.url, user=db_map.username, password=db_map.password,
                         database=db_map.db).query_to_dict(
        query="select * from maintenance_deploy_config where service_name = %(service_name)s ",
        params={"service_name": service_name})
    print(f'输入serviceName: {service_name}, 找到{len(dbinfo)}个配置项')
    return dbinfo

# 2.
def cloneAndBuildProject():
    # 从配置文件中读取git信息
    git_info = yaml.query_and_map("project.git")
    base_clone_path = git_info.base_clone_path
    git = GitUtils(git_url=git_info.url,
                   username=git_info.username,
                   password=git_info.password,
                   build_base_path=base_clone_path,
                   instance_id=git_info.version)
    git.clone_java_project(git.get_git_credentials())
    git.build_java_project_package()


# 3. 根据项目类型，执行构建
# 4. 根据配置文件中的参数部署到对应服务器并启动
# 5. Http进行请求测试，并将发布结果推送到钉钉


# ip = '192.168.0.71'
# user = 'root'
# pwd = ('wyz123!@#')
#
# # 远程登录
# logging.basicConfig(level=logging.INFO)
# shell = contnet_shell(ip, user, pwd)

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
ip = 'localhost'
port = '9200'
uri = '/test/isOk'

try:
    res = HttpUtils.get(ip, port, uri)
except Exception as e:
    raise e
if (res.status_code == 200):
    print('成功！！！\n')
else:
    print(f'返回值：{res.status_code}, 容器启动不成功\n')
shell.close_cont()

if __name__ == '__main__':
    run()
#     # # 1. 加载yaml，
#     data = YamlUtils.get_value(absolute_path, "deploy_names")
#     if not data:
#         print("你需要在config.yaml中填入deploy_names:发布列表")
#     else:
#         print(f"读取到deploy配置：{data}，开始构建")
#         for service_name in data:
#             # 2. 读取数据库配置文件
#             service_db_infos = getProjectInfo(service_name)
#             if not service_db_infos:
#                 # 3. 根据配置文件中的信息，调用git工具clone项目
#                 cloneAndBuildProject()
#                 # # build_java_project()
#                 # for project_db_info in project_db_infos:
#                 #     print()

__all__ = ['git_utils', 'shell_utils']
