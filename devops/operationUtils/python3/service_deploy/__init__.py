#!/user/bin/env python
# -*-coding:utf-8-*-
import logging
import os
import shutil
import subprocess
import sys
import time
from operator import itemgetter
from pathlib import Path

import proc

from devops.operationUtils.python3.mysql_slow_warn.slow_mysql_groupchat_robot import DingdingGroupchat
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
else:
    logging.info("当前读取的配置文件名为：%s", config_name)
# 获取当前工作目录的绝对路径
current_working_directory = os.getcwd()
# 构建相对路径的绝对路径读取配置文件目录的yaml配置
config_absolute_path = os.path.abspath(os.path.join(current_working_directory, 'config', f'{config_name}.yaml'))
yaml = YamlUtils(config_absolute_path)
clone_absolute_path = None


def run():
    """
    1.clone项目
    2.按照deploy构建。
    3.获取对应的部署清单(mysql)
    4.推送，并启动，测试，发送消息。
    """
    # 1. clone项目
    logging.info("clone项目")
    clone_build_project()

    # 2. 构建（Java And Vue）
    logging.info("开始打包Java")
    package_java_result = build_java_project_package()
    logging.info("构建完成，准备上传Java jar到服务器, %s", package_java_result)
    deploy_java(package_java_result)

    logging.info("开始打包Vue2")
    package_vue_result = build_vue_project_package()
    logging.info("构建完成，准备上传Vue dist到服务器, %s", package_java_result)
    deploy_vue(package_vue_result)

    # for deploy_name in deploy_names:
    #     logging.info("读取mysql部署信息：%s", deploy_name)
    #     # 获取到此服务的部署列表
    #     projects = getProjectInfo(deploy_name)
    #     if not projects:
    #         for project in projects:
    #             (deploy_ip,
    #              depoly_ssh_port,
    #              deploy_base_path_linux,
    #              deploy_file_path,
    #              service_type,
    #              deploy_user_name,
    #              deploy_password) = itemgetter("deploy_ip",
    #                                            "depoly_ssh_port",
    #                                            "deploy_base_path_linux",
    #                                            "deploy_file_path",
    #                                            "service_type",
    #                                            "deploy_user_name",
    #                                            "deploy_password")(project)
    #
    #             shell_client = contnet_shell(deploy_ip, deploy_user_name, deploy_password)
    #             shell_client.copy_file(os.path.join(package, ), os.path.join(deploy_base_path_linux, deploy_file_path))

    # getProjectInfo()


"""
输入service_name，获取此服务的部署清单  List<Dict>
"""


def get_project_info(service_name, project_name, service_type: str = '1'):
    db_dict = yaml.query("base.config.db")
    logging.info("读取到base.config.db的配置为：%s", db_dict)
    # 读取mysql对应的项目配置
    dbinfo = MySQLHelper(host=db_dict["url"], user=db_dict["username"], password=db_dict["password"],
                         database=db_dict["db"]).query_to_dict(
        query="""
                select * from maintenance_deploy_config
                where service_name = %(service_name)s and project_name = %(project_name)s and service_type = %(service_type)s 
               """,
        params={"service_name": service_name, "project_name": project_name, "service_type": service_type})
    logging.info('输入serviceName: %s, 找到%s个配置项', service_name, len(dbinfo))
    logging.debug("具体配置项为：%s", dbinfo)
    return dbinfo


"""
@return result:构建的java包的绝对路径地址
"""


def build_java_project_package():
    # 读取配置文件中的service_name
    deploy_names = yaml.query("deploy.java.deploy_names")
    project_name = yaml.get("project.git.project_name")
    logging.info("读取本次发版清单为：%s, %s", deploy_names, type(deploy_names))
    if deploy_names:
        services = []
        for service_name in deploy_names:
            logging.info("读取mysql部署信息，serviceName:%s", service_name)
            infos = get_project_info(service_name, project_name, "1")
            if not infos:
                logging.error("没有读取到mysql中存在对应的Java项目配置！service_name: %s", service_name)
            else:
                services.extend(infos)
            # 遍历每一个部署信息
            for project in infos:
                (deploy_ip,
                 deploy_ssh_port,
                 deploy_base_path_linux,
                 deploy_file_path,
                 service_type,
                 deploy_user_name,
                 deploy_password) = itemgetter("deploy_ip",
                                               "deploy_ssh_port",
                                               "deploy_base_path_linux",
                                               "deploy_file_path",
                                               "service_type",
                                               "deploy_user_name",
                                               "deploy_password")(project)

        logging.info("循环结束, %s", services)
        # 直接提取去重后的id列表（保留最后出现的元素）
        unique_ids = list({item["maven_module_uri"]: None for item in services}.keys())
        logging.info("去重的结果：%s", unique_ids)

        """构建 Java 项目（支持 Maven 和 Gradle）"""
        try:
            # 检查项目类型（Maven 或 Gradle）
            if os.path.exists(os.path.join(clone_absolute_path, "pom.xml")):
                logging.info("输入的deploynames: %s, 标识位: %s", deploy_names, unique_ids)
                build_cmd = ["mvn", "clean", "package -am -pl", ",".join(unique_ids)]
                logging.info("检测到 Maven 项目")
                resultUrl = os.path.join(clone_absolute_path, "dist")
            # elif os.path.exists(os.path.join(self.project_dir, "build.gradle")) or \
            #         os.path.exists(os.path.join(self.project_dir, "build.gradle.kts")):
            #     print("检测到 Gradle 项目")
            #     # 使用 wrapper 或系统安装的 Gradle
            #     gradle_cmd = "./gradlew" if os.path.exists(os.path.join(self.project_dir, "gradlew")) else "gradle"
            #     build_cmd = [gradle_cmd, "clean", "build"]
            else:
                logging.error("未找到 Maven项目POM文件")
                return False

            logging.info(f"开始构建项目: {' '.join(build_cmd)}, cwd: {clone_absolute_path}")
            # 检查 mvn 命令是否存在
            if not shutil.which("mvn"):
                raise RuntimeError("未找到 Maven 命令，请确保已安装并配置 PATH")

            if os.path.exists(clone_absolute_path):
                logging.debug("路径存在")
            else:
                logging.debug(f"路径不存在: {clone_absolute_path}")

            result = subprocess.run(
                " ".join(build_cmd),
                cwd=clone_absolute_path,
                shell=True,
                check=True,
                text=True,
                capture_output=True
            )

            # subprocess.Popen
            # # 循环读取输出
            # while True:
            #     out = result.stdout.readline()
            #     err = result.stderr.readline()
            #     if out == '' and err == '':
            #         break
            #     if out:
            #         print('stdout:', out.strip())
            #     if err:
            #         print('stderr:', err.strip())
            #
            # # 等待进程结束
            # result.wait()

            logging.info("构建成功")
            logging.info("构建输出: %s", result.stdout)
            return {"is_success": True, "result": services}
        except subprocess.CalledProcessError as e:
            logging.exception(f"构建失败: {e.stderr}")
            return {"is_success": False, "result": []}
    else:
        logging.error("请配置deploy.java.deploy_names")
        return {"is_success": True, "result": []}


"""
    部署Java项目
"""


def deploy_java(package_java_result):
    if package_java_result and package_java_result["is_success"]:
        for package in package_java_result["result"]:
            (
                deploy_ip, deploy_ssh_port, deploy_user_name,
                deploy_password, deploy_os_type, deploy_file_path, service_code, springboot_http_port, jvm_config
                , service_name, service_type
            ) = (
                package["deploy_ip"], int(package["deploy_ssh_port"]),
                package["deploy_user_name"], package["deploy_password"],
                package["deploy_os_type"], package["deploy_file_path"],
                package["service_code"], package["springboot_http_port"],
                package["jvm_config"], package["service_name"],
                package["service_type"]
            )
            deploy_base_path = package["deploy_base_path_linux"] if deploy_os_type == "1" else package[
                "deploy_base_path_windows"]
            deploy_file_path = deploy_file_path if deploy_file_path != None else ""

            shell = contnet_shell(hostname=deploy_ip, port=deploy_ssh_port, username=deploy_user_name,
                                  password=deploy_password)
            # 获取目标服务器系统对应的文件路径分隔符
            directory_separator = shell.get_directory_separator()
            # 拼接部署根路径+ 文件相对路径
            target_server_path = deploy_base_path + directory_separator + deploy_file_path + directory_separator

            logging.info("开始上传，目标服务器：%s, service_code: %s, 本地构建目录：%s, 目标服务器地址： %s",
                         deploy_ip,
                         service_code,
                         os.path.join(clone_absolute_path, "dist", service_code + ".jar"),
                         target_server_path + service_code)
            try:
                if service_type == "1":
                    # 上传java
                    upload = shell.copy_file(os.path.join(clone_absolute_path, "dist", service_code + ".jar"),
                                             target_server_path, service_code + ".jar")
                    server_port = f'--server.port={springboot_http_port}' if springboot_http_port else ''
                    jvm_params = f' {jvm_config}' if jvm_config else ''

                    if upload:
                        old_prc_id = shell.exec_cmd(
                            f"ps -ef | grep {service_code} | grep -v grep | grep -v bash | awk" + ' \'{print $2}\'')

                        if old_prc_id and old_prc_id[1]:
                            logging.info("检测到有存在的服务进程：%s", old_prc_id)
                            shell.exec_cmd(f"kill -9 {old_prc_id[1]}")
                            logging.info("杀死进程号：%s", old_prc_id[1])

                        logging.info("%s,准备启动服务：%s", deploy_ip, service_code)
                        cmd = shell.exec_cmd(
                            f"nohup setsid java -jar {service_code + '.jar'} {server_port} {jvm_params} > {service_code + '.log'} 2>&1 &",
                            target_server_path)
                        # cmd = shell.exec_cmd(f"java -version", target_server_path)
                        # cmd = shell.exec_cmd(f"bash -lc \'java -jar {service_code + '.jar'} \' ", target_server_path)
                        logging.info("%s, 启动结果：%s", deploy_ip, cmd)
                        time.sleep(5)  # 等待进程启动
                        send_msg(f"{service_name}，已发布到服务器：{deploy_ip}")
                    else:
                        err_msg = f"(上传失败！服务：{service_code}，目标服务器：{deploy_ip}，目标路径：{target_server_path})"
                        logging.error(err_msg)
                        raise Exception(err_msg)
                else:
                    logging.info(f"当前的服务serviceType不识别，service_type: {service_type}")
            except Exception as e:
                logging.exception(e)
                # 发送通知
                send_msg(f"{service_name}，发布失败：{deploy_ip}, 错误信息：{e}")

            # 关闭shell避免泄露
            shell.close_cont()
            shell = None
    else:
        logging.info("没有接收到正确的java打包信息：%s", package_java_result)


"""
    构建打包VUE项目
"""


def build_vue_project_package():
    # 读取配置文件中的service_name
    deploy_vue_config = yaml.query("deploy.vue")
    deploy_names = deploy_vue_config['deploy_names']
    project_name = yaml.get("project.git.project_name")
    logging.info("读取本次发版的vue service_name为：%s, %s", deploy_names, type(deploy_names))

    if deploy_names and type(deploy_names) is str:
        logging.info("读取mysql中的vue部署信息，serviceName:%s", deploy_names)
        infos = get_project_info(deploy_names, project_name, "2")

        if not infos or len(infos) == 0:
            logging.error("没有读取到mysql中存在对应的vue项目配置！service_name: %s", deploy_names)
            return {"is_success": False, "result": []}

        project_result_url = os.path.join(clone_absolute_path, deploy_vue_config['uri'])
        info = infos[0]
        try:
            # 检查项目类型（package.json文件）
            if os.path.exists(os.path.join(project_result_url, "package.json")):
                logging.info("在目录【%s】中找到了对应的package.json文件", project_result_url)
                build_step_one_cmd = ["npm install"]
                logging.info("开始执行构建动作，构建命令：%s", build_step_one_cmd)
                build_step_two_cmd = ["npm", "run", f"{info['web_script']}", "--registry=https://registry.npmmirror.com"]

                step_one_result = subprocess.run(
                    " ".join(build_step_one_cmd),
                    cwd=project_result_url,
                    shell=True,
                    check=True,
                    text=True,
                    capture_output=True
                )
                logging.info("step_one_result构建输出: %s，异常：%s", step_one_result.stdout, step_one_result.stderr)

                logging.info("开始执行step_two: %s", build_step_two_cmd)
                step_two_result = subprocess.run(
                    " ".join(build_step_two_cmd),
                    cwd=project_result_url,
                    shell=True,
                    check=True,
                    text=True,
                    capture_output=True
                )
                logging.info("step_two_result构建输出: %s", step_two_result.stdout)

                if os.path.exists(os.path.join(project_result_url, "dist.zip")):
                    logging.info("构建成功")
                    return {"is_success": True, "result": infos}
                else:
                    logging.error("没有找到对应的vue工程dist文件！")
            else:
                logging.error("没有找到package.json文件")
                return {"is_success": False, "result": []}
        except Exception as e:
            logging.exception("构建vue工程报错了，%s", e)


"""
    部署VUE项目
"""


def deploy_vue(package_vue_result):
    deploy_vue_config = yaml.query("deploy.vue")
    if package_vue_result and package_vue_result["is_success"]:
        for package in package_vue_result["result"]:
            (
                deploy_ip, deploy_ssh_port, deploy_user_name,
                deploy_password, deploy_os_type, deploy_file_path, service_code, springboot_http_port, jvm_config
                , service_name, service_type
            ) = (
                package["deploy_ip"], int(package["deploy_ssh_port"]),
                package["deploy_user_name"], package["deploy_password"],
                package["deploy_os_type"], package["deploy_file_path"],
                package["service_code"], package["springboot_http_port"],
                package["jvm_config"], package["service_name"],
                package["service_type"]
            )
            deploy_base_path = package["deploy_base_path_linux"] if deploy_os_type == "1" else package[
                "deploy_base_path_windows"]
            deploy_file_path = deploy_file_path if deploy_file_path != None else ""

            shell = contnet_shell(hostname=deploy_ip, port=deploy_ssh_port, username=deploy_user_name,
                                  password=deploy_password)
            # 获取目标服务器系统对应的文件路径分隔符
            directory_separator = shell.get_directory_separator()
            # 拼接部署根路径+ 文件相对路径
            target_server_path = deploy_base_path + directory_separator + deploy_file_path + directory_separator

            logging.info("开始上传，目标服务器：%s, service_code: %s, 本地构建目录：%s, 目标服务器地址： %s",
                         deploy_ip,
                         service_code,
                         os.path.join(clone_absolute_path, deploy_vue_config['uri'], "dist.zip"),
                         target_server_path + service_code)
            try:
                if service_type == "2":
                    command = 'nginx'
                    if not package['web_proxy_server_path']:
                        command = package['web_proxy_server_path']
                    exec_cmd = shell.exec_cmd(f'{command} -version')
                    if exec_cmd.out_res.find('nginx') == '-1':
                        raise Exception(f'没有找到对应的nginx路径，执行结果为：{exec_cmd}')

                    # 上传Vue2 Dist包到web代理服务器
                    upload = shell.copy_file(os.path.join(clone_absolute_path, deploy_vue_config['uri'], "dist.zip"),
                                             target_server_path, "dist.zip")
                    logging.info(
                        f"已经将文件从【{os.path.join(clone_absolute_path, deploy_vue_config['uri'], 'dist.zip')}】，上送到{target_server_path}目录下")

                    if upload:
                        logging.info("%s,准备启动服务：%s", deploy_ip, service_code)
                        cmd = shell.exec_cmd(f'{command} -s reload')
                        # cmd = shell.exec_cmd(f"java -version", target_server_path)
                        # cmd = shell.exec_cmd(f"bash -lc \'java -jar {service_code + '.jar'} \' ", target_server_path)
                        logging.info("%s, 启动结果：%s", deploy_ip, cmd)
                        send_msg(f"{service_name}，已发布到服务器：{deploy_ip}")
                    else:
                        err_msg = f"(上传失败！服务：{service_code}，目标服务器：{deploy_ip}，目标路径：{target_server_path})"
                        logging.error(err_msg)
                        raise Exception(err_msg)
                else:
                    logging.info(f"当前的服务serviceType不识别，service_type: {service_type}")
            except Exception as e:
                logging.exception(e)
                # 发送通知
                send_msg(f"{service_name}，发布失败：{deploy_ip}, 错误信息：{e}")

            # 关闭shell避免泄露
            shell.close_cont()
            shell = None
    else:
        logging.info("没有接收到正确的vue打包信息：%s", package_vue_result)


# 2.
def clone_build_project():
    # 声明全局变量（需要修改的）
    global clone_absolute_path
    # 从配置文件中读取git信息
    git_info = yaml.query("project.git")
    logging.info("读取到的git配置为：%s", git_info)
    git = GitUtils(git_url=git_info['url'],
                   username=git_info['username'],
                   password=git_info['password'],
                   build_base_path=git_info['base_clone_path'],
                   instance_id=git_info['version'],
                   project_name=git_info['project_name']
                   )
    clone_absolute_path = git.clone_java_project(git.get_git_credentials(), git_info['branch'])


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
# res = ""
# ip = 'localhost'
# port = '9200'
# uri = '/test/isOk'
#
# try:
#     res = HttpUtils.get(ip, port, uri)
# except Exception as e:
#     raise e
# if (res.status_code == 200):
#     print('成功！！！\n')
# else:
#     print(f'返回值：{res.status_code}, 容器启动不成功\n')
# shell.close_cont()

"""
获取对应的maven路径，避免执行shell的时候出一些这那那这的path问题：
当使用shell[]的时候如果path没有Maven路径，那么就不好使，恶心死人了
"""


def find_maven_path() -> str:
    """优先通过 MAVEN_HOME 查找，再自动检测"""
    # 1. 优先使用 MAVEN_HOME
    maven_home = os.environ.get("MAVEN_HOME")
    if maven_home:
        maven_bin = os.path.join(maven_home, "bin", "mvn")
        logging.info("maven_home: %s", maven_bin)
        if os.path.exists(maven_bin):
            # return maven_bin
            return "mvn"

    # 2. 从系统 PATH 查找
    path_from_env = shutil.which("mvn")
    if path_from_env:
        # return path_from_env
        return "mvn"
    # 3. 扫描常见安装路径（Windows）
    common_paths = [
        r"C:\Program Files\Apache Maven\bin\mvn.exe",
        r"C:\Program Files (x86)\Apache Maven\bin\mvn.exe",
        str(Path.home() / "apache-maven" / "bin" / "mvn.exe"),
    ]
    for path in common_paths:
        if os.path.exists(path):
            return path

    raise FileNotFoundError("未找到 Maven，请配置 MAVEN_HOME 或安装 Maven。")


def send_msg(msg):
    msg_type = yaml.query("message.type")
    if msg_type == "ding_group":
        ding_group_config = yaml.query("message.config.ding_group")
        (DingdingGroupchat(ding_group_config['access_token'], ding_group_config['secret'])
         .send(msg))
    elif msg_type == "qwx":
        logging.info("消息发送暂不支持qwx模式")


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
