#!/user/bin/env python
# -*-coding:utf-8-*-
import pymysql
from typing import List, Dict, Any, Optional, Union, TypeVar

T = TypeVar('T')


class MySQLHelper:
    """简化版 MySQL 连接工具，支持灵活返回字典或对象"""

    def __init__(self, host: str, user: str, password: str, database: str,
                 port: int = 3306, charset: str = 'utf8mb4'):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.port = port
        self.charset = charset

    def _connect(self):
        return pymysql.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            database=self.database,
            port=self.port,
            charset=self.charset,
            cursorclass=pymysql.cursors.DictCursor
        )

    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """执行查询并返回字典列表"""
        with self._connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params or {})
                return cursor.fetchall()

    def execute_update(self, query: str, params: Optional[Dict[str, Any]] = None) -> int:
        """执行更新操作（INSERT, UPDATE, DELETE）"""
        with self._connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params or {})
                conn.commit()
                return cursor.rowcount

    def query_to_dict(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """执行查询并返回字典列表（别名方法，增强可读性）"""
        return self.execute_query(query, params)

    def query_to_object(self, query: str, params: Optional[Dict[str, Any]] = None, obj_type: type = None) -> List[Any]:
        """执行查询并将结果转换为对象列表（保留原功能）"""
        results = self.execute_query(query, params)
        if not results or not obj_type:
            return results

        return [self._dict_to_obj(row, obj_type) for row in results]

    def _dict_to_obj(self, data: Dict[str, Any], obj_type: type) -> Any:
        """将字典转换为对象"""
        obj = obj_type()
        for key, value in data.items():
            if hasattr(obj, key):
                setattr(obj, key, value)
        return obj


# 使用示例
if __name__ == "__main__":
    db = MySQLHelper(
        host='192.168.0.69',
        user='root',
        password='000000',
        database='ry-cloud'
    )

    # 方式1: 直接返回字典（无需定义类）
    users = db.query_to_dict("SELECT * FROM maintenance_deploy_config", {"age": 25})
    for dbobj in users:
        print(dbobj["project_name"], dbobj["service_name"])  # 直接通过字典键访问


    # # 方式2: 返回对象（保留原功能）
    # class User:
    #     def __init__(self):
    #         self.id = None
    #         self.name = None
    #         self.age = None
    #
    #
    # users_as_objects = db.query_to_object("SELECT * FROM users", obj_type=User)
    # for user in users_as_objects:
    #     print(user.name, user.age)  # 通过对象属性访问