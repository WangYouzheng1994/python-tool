### bs解析
- 解析原理
1. 标签定位
2. 提取标签、标签属性中存储的数据值
- bs4数据解析的原理：
1. 实例化一个BeautifulSoup对象，并且将页面源码数据加载到该对象中
2. 通过调用BeautifulSoup对象中相关的属性或者方法进行标签定位和数据提取
- 环境安装
> 设置全局pip源 pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple  
- `pip install bs4`
- `pip install lxml`
3. 如何实例化BeautifulSoup对象：
```
from bs4 import BeautifulSoup
```
- 对象的实例化：
  1. 将本地的html文档中的数据加载到该对象中:
  ```
  fp = open('./test.html', 'r', encoding='uft-8')
  soup = BeautifulSoup(fp, 'lxml')
  ```
  
  2. 将互联网抓到的html文档源码加载到该对象中
  ```
  page_text = response.text
  soup = BeatifulSoup(page_text, 'lxml')
  ```

### 数据解析的方法和属性
