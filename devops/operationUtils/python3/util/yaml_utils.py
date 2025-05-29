#!/user/bin/env python
# -*-coding:utf-8-*-

import os
import yaml
from typing import Dict, Any, Optional, Union, List, TypeVar, Type

T = TypeVar('T')

class YamlUtils:
    """YAML文件操作工具类，支持对象化调用"""
    def __init__(self, file_path: str, encoding: str = 'utf-8'):
        """初始化YAML工具实例"""
        self.file_path = file_path
        self.encoding = encoding

    def read(self) -> Optional[Dict[str, Any]]:
        """读取YAML文件并返回字典"""
        return YamlUtils.read_yaml(self.file_path, self.encoding)

    def exists(self, key_path: str) -> bool:
        """检查YAML文件中是否存在指定路径的键"""
        return YamlUtils.key_exists(self.file_path, key_path)

    def get(self, key_path: str, default: Any = None) -> Any:
        """获取YAML文件中指定路径的值"""
        return YamlUtils.get_value(self.file_path, key_path, default)

    def query(self, key_path: str, obj_type: Type[T]) -> Optional[T]:
        """
        查询指定key下的所有参数，并映射为对象

        Args:
            key_path: 键路径（如 "database.config"）
            obj_type: 目标对象类型

        Returns:
            映射后的对象实例，若key不存在则返回None
        """
        return YamlUtils.query_and_map(self.file_path, key_path, obj_type)

    """YAML文件操作工具类，支持静态方法调用"""
    @staticmethod
    def read_yaml(file_path: str, encoding: str = 'utf-8') -> Optional[Dict[str, Any]]:
        """
        读取YAML文件并返回字典

        Args:
            file_path: YAML文件路径
            encoding: 文件编码，默认为utf-8

        Returns:
            解析后的字典数据，如果文件不存在则返回None
        """
        if not os.path.exists(file_path):
            print(f"错误: 文件 '{file_path}' 不存在")
            return None

        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"读取YAML文件失败: {e}")
            return None

    @staticmethod
    def write_yaml(data: Dict[str, Any], file_path: str,
                   encoding: str = 'utf-8', sort_keys: bool = False) -> bool:
        """
        将字典写入YAML文件

        Args:
            data: 要写入的字典数据
            file_path: 目标YAML文件路径
            encoding: 文件编码，默认为utf-8
            sort_keys: 是否按键排序，默认为False

        Returns:
            写入成功返回True，失败返回False
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            with open(file_path, 'w', encoding=encoding) as f:
                yaml.dump(data, f, allow_unicode=True, sort_keys=sort_keys)
            return True
        except Exception as e:
            print(f"写入YAML文件失败: {e}")
            return False

    @staticmethod
    def merge_yaml(source_file: str, target_file: str,
                   encoding: str = 'utf-8') -> bool:
        """
        将源YAML文件合并到目标YAML文件

        Args:
            source_file: 源YAML文件路径
            target_file: 目标YAML文件路径
            encoding: 文件编码，默认为utf-8

        Returns:
            合并成功返回True，失败返回False
        """
        # 读取源文件和目标文件
        source_data = YamlUtils.read_yaml(source_file, encoding)
        target_data = YamlUtils.read_yaml(target_file, encoding) or {}

        if source_data is None:
            return False

        # 合并数据（递归更新）
        merged_data = YamlUtils._deep_merge(target_data, source_data)

        # 写入合并后的文件
        return YamlUtils.write_yaml(merged_data, target_file, encoding)

    @staticmethod
    def _deep_merge(target: Dict[str, Any], source: Dict[str, Any]) -> Dict[str, Any]:
        """
        递归合并两个字典

        Args:
            target: 目标字典
            source: 源字典

        Returns:
            合并后的字典
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                target[key] = YamlUtils._deep_merge(target[key], value)
            else:
                target[key] = value
        return target

    @staticmethod
    def get_value(file_path: str, key_path: str, default: Any = None) -> Any:
        """
        获取YAML文件中指定路径的值

        Args:
            file_path: YAML文件路径
            key_path: 键路径，使用点分隔（例如: "database.host"）
            default: 默认值，如果键不存在则返回此值

        Returns:
            指定路径的值，如果不存在则返回default
        """
        data = YamlUtils.read_yaml(file_path)
        if data is None:
            return default

        keys = key_path.split('.')
        current = data

        for key in keys:
            if not isinstance(current, dict) or key not in current:
                return default
            current = current[key]

        return current

    @staticmethod
    def query_and_map(file_path: str, key_path: str, obj_type: Type[T]) -> Optional[T]:
        """
        查询指定key下的所有参数，并映射为对象

        Args:
            file_path: YAML文件路径
            key_path: 键路径，使用点分隔（例如: "database.config"）
            obj_type: 目标对象类型

        Returns:
            映射后的对象实例，如果key不存在则返回None
        """
        if not YamlUtils.key_exists(file_path, key_path):
            return None

        # 获取指定key下的数据
        data = YamlUtils.get_value(file_path, key_path)

        # 创建对象实例
        obj = obj_type()

        # 将字典键值对映射到对象属性
        if isinstance(data, dict):
            for key, value in data.items():
                if hasattr(obj, key):
                    setattr(obj, key, value)
            return obj
        else:
            print(f"错误: 指定key '{key_path}' 下的数据不是字典类型")
            return None


# 使用示例
if __name__ == "__main__":
    # 示例YAML文件内容
    # test.yaml:
    # database:
    #   host: localhost
    #   port: 3306
    #   credentials:
    #     username: root
    #     password: secret

    # 读取YAML文件
    data = YamlUtils.read_yaml("test.yaml")
    print("完整数据:", data)

    # 获取嵌套值
    host = YamlUtils.get_value("test.yaml", "database.host")
    print("数据库主机:", host)

    # 获取不存在的键
    timeout = YamlUtils.get_value("test.yaml", "database.timeout", default=30)
    print("默认超时:", timeout)

    # 写入YAML文件
    new_data = {
        "app": {
            "name": "MyApp",
            "version": "1.0.0"
        }
    }
    YamlUtils.write_yaml(new_data, "config.yaml")

    # 合并YAML文件
    YamlUtils.merge_yaml("test.yaml", "config.yaml")