### 使用requests发请求
- 安装依赖
> pip install requests -i https://pypi.tuna.tsinghua.edu.cn/simple

- requests做爬虫的几个步骤
1. 定义url
2. 发起请求（http request）
3. 获取请求的响应实例中的数据（http response)
4. 持久化存储响应数据



### 关于工程类文件编写的一些说明
1. 头部
```
#!/user/bin/env python
# -*- coding:utf-8 -*-
```
- 说明指定unix系统环境下 找到对应的 python命令。
- 说明此文件编码需要用utf-8 https://zhuanlan.zhihu.com/p/562394533?utm_id=0


### 防爬策略与方案
1. UA (User-Agent)检测
> UA伪装：让爬虫对应的请求载体身份标识伪装成某一款浏览器
```

```


### 聚焦爬虫
数据解析分类：
- 正则
- bs4
- xpath(***)