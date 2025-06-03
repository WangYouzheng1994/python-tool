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

    def query(self, key_path: str, obj_type: Optional[Type[T]] = None) -> Union[Optional[T], Dict[str, Any]]:
        """
        查询指定key下的所有参数

        Args:
            key_path: 键路径（如 "database.config"）
            obj_type: 目标对象类型，可选参数

        Returns:
            - 若指定obj_type: 映射后的对象实例
            - 若未指定obj_type: 原始字典结构
            - 若key不存在: None
        """
        if not self.exists(key_path):
            return None

        data = self.get(key_path)

        if obj_type:
            return self._map_to_object(data, obj_type)
        else:
            return data

    def write(self, data: Dict[str, Any], sort_keys: bool = False) -> bool:
        """将字典写入YAML文件"""
        return YamlUtils.write_yaml(data, self.file_path, self.encoding, sort_keys)

    def merge(self, source_file: str = None) -> bool:
        """将源YAML文件合并到当前YAML文件"""
        source = source_file or self.file_path
        return YamlUtils.merge_yaml(source, self.file_path, self.encoding)

    # 静态方法保持不变...
    @staticmethod
    def read_yaml(file_path: str, encoding: str = 'utf-8') -> Optional[Dict[str, Any]]:
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
    def key_exists(file_path: str, key_path: str) -> bool:
        data = YamlUtils.read_yaml(file_path)
        if data is None:
            return False

        keys = key_path.split('.')
        current = data

        for key in keys:
            if not isinstance(current, dict) or key not in current:
                return False
            current = current[key]

        return True

    @staticmethod
    def get_value(file_path: str, key_path: str, default: Any = None) -> Any:
        if not YamlUtils.key_exists(file_path, key_path):
            return default

        data = YamlUtils.read_yaml(file_path)
        keys = key_path.split('.')
        current = data

        for key in keys:
            current = current[key]

        return current

    @staticmethod
    def query_and_map(file_path: str, key_path: str, obj_type: Type[T]) -> Optional[T]:
        if not YamlUtils.key_exists(file_path, key_path):
            return None

        data = YamlUtils.get_value(file_path, key_path)
        obj = obj_type()

        if isinstance(data, dict):
            for key, value in data.items():
                if hasattr(obj, key):
                    setattr(obj, key, value)
            return obj
        else:
            print(f"错误: 指定key '{key_path}' 下的数据不是字典类型")
            return None

    @staticmethod
    def write_yaml(data: Dict[str, Any], file_path: str,
                   encoding: str = 'utf-8', sort_keys: bool = False) -> bool:
        try:
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
        source_data = YamlUtils.read_yaml(source_file, encoding)
        target_data = YamlUtils.read_yaml(target_file, encoding) or {}

        if source_data is None:
            return False

        merged_data = YamlUtils._deep_merge(target_data, source_data)
        return YamlUtils.write_yaml(merged_data, target_file, encoding)

    @staticmethod
    def _deep_merge(target: Dict[str, Any], source: Dict[str, Any]) -> Dict[str, Any]:
        """递归合并两个字典"""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                target[key] = YamlUtils._deep_merge(target[key], value)
            else:
                target[key] = value
        return target

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