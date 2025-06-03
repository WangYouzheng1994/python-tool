#!/user/bin/env python
# -*-coding:utf-8-*-
import logging
import os
import subprocess
from getpass import getpass
from pathlib import Path

from devops.operationUtils.python3.util.mysql_pool_utils import  MySQLHelper
from devops.operationUtils.python3.util.yaml_utils import YamlUtils


class GitUtils:
    def __init__(self, git_url, build_base_path, project_name, username="", password="", instance_id=""):
        self.project_url = None
        self.git_url = git_url
        self.username = os.environ.get("GIT_USERNAME")
        self.password = os.environ.get("GIT_PASSWORD")

        if self.username == "":
            self.username = input("Git Username: ")
        if self.password == "":
            self.password = getpass("Git Password: ")

        self.project_name = project_name
        self.build_base_path = build_base_path
        self.instance_id = str(instance_id)
    """
    拉取项目
    """
    # def getProjectByHttp(self, projectNames=[], moduleName=None):
    #     self.get_git_credentials()
    #     if not projectNames:
    #         # 读取YAML文件
    #         data = YamlUtils.get_value(self.absolute_path, "deploy_names")
    #         if not data:
    #             print("你需要在config.yaml中填入deploy_names:发布列表")
    #         else :
    #             print(f"读取到deploy配置：{data}")
    #             for project in data:
    #                 project_db_infos = self.getProjectInfo(project)
    #                 if not project_db_infos:
    #                     self.clone_java_project()
    #                     self.build_java_project()
    #                     for project_db_info in project_db_infos:
    #                          print()
        # else:
        #     for project in projectNames:
        #         print(project)

        # self.build_java_project()


    def getProjectInfo(self, service_name):
        # 读取mysql对应的项目配置
        dbinfo = MySQLHelper(host='192.168.0.69', user='root', password='000000', database='ry-cloud').query_to_dict(
            query="select * from maintenance_deploy_config where service_name = %(service_name)s ",
            params={"service_name": service_name})
        print(f'输入serviceName: {service_name}, 找到{len(dbinfo)}个配置项')
        return dbinfo

    """
    获取Git认证信息
    """
    def get_git_credentials(self, auth_method=1):
        """获取Git认证信息（支持HTTPS和SSH）"""
        # auth_method = input("选择认证方式 (1=HTTPS, 2=SSH): ")

        if auth_method == "1":
            return {"method": "https", "username": self.username, "password": self.password}
        else:
            print("请确保已配置SSH密钥并添加到ssh-agent")
            return {"method": "ssh"}

    def clone_java_project(self, credentials=None):
        """从 Git 拉取 Java 项目"""
        try:
            # 处理HTTPS认证
            if credentials and credentials["method"].lower() in ["http"]:
                # 替换URL为认证URL
                auth_url = self.git_url.replace(
                    "http://",
                    f"http://{credentials['username']}:{credentials['password']}@"
                )
            else:
                auth_url = self.git_url

            # 创建目标目录（如果不存在）
            logging.info("clone_absolute_path，项目克隆目录为： %s,%s,%s", self.build_base_path, self.project_name, self.instance_id)
            clone_absolute_path = os.path.join(self.build_base_path, self.project_name, self.instance_id)
            Path(clone_absolute_path).mkdir(parents=True, exist_ok=True)

            # 检查目录是否为空
            if not os.listdir(clone_absolute_path):
                print(f"正在克隆项目: {self.git_url}")
                subprocess.run(
                    ["git", "clone", self.git_url, clone_absolute_path],
                    check=True,
                    text=True,
                    stderr=subprocess.PIPE
                )
                print("克隆完成")
            else:
                print("目录非空，尝试拉取最新代码")
                subprocess.run(
                    ["git", "-C", clone_absolute_path, "pull"],
                    check=True,
                    text=True,
                    stderr=subprocess.PIPE
                )
                print("拉取完成")

            self.project_dir = clone_absolute_path
            return clone_absolute_path
        except subprocess.CalledProcessError as e:
            print(f"Git 操作失败: {e.stderr}")
            return None




# 测试示例
if __name__ == "__main__":
    GIT_URL = "http://144.123.43.78:9208/gitlab/huangxupeng0831/dataplatform-ruoyi.git"  # 替换为实际的 Git 仓库 URL
    utils = GitUtils(GIT_URL)
    utils.getProjectByHttp()

    #
    # credentials = utils.get_git_credentials();
    # project_dir = utils.clone_java_project(GIT_URL, credentials=credentials)
    #
    # if project_dir:
    #     build_success = utils.build_java_project(project_dir)
    #     print(f"项目构建状态: {'成功' if build_success else '失败'}")