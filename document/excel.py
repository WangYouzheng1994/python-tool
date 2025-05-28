#!/user/bin/env python
# -*-coding:utf-8-*-
"""基于python 生成带图表的Excel"""

import pandas as pd
import matplotlib.pyplot as plt
from openpyxl import Workbook
from openpyxl.drawing.image import Image

# 设置字体
try:
    # 尝试指定可用字体
    plt.rcParams["font.family"] = ["SimHei", "WenQuanYi Micro Hei", "Heiti TC", "Arial"]
except:
    # 备选方案
    plt.rcParams["font.family"] = ["sans-serif"]
    plt.rcParams["axes.unicode_minus"] = False

# 读取Excel数据
data = pd.read_excel('input.xlsx')

# 假设数据有两列：产品和销售额
products = data['产品']
sales = data['销售额']

# 生成柱状图
plt.bar(products, sales)
plt.xlabel('产品')
plt.ylabel('销售额')
plt.title('产品销售额统计')
# 保存图表为图片
plt.savefig('sales_chart.png')
plt.close()

# 创建新的Excel工作簿
wb = Workbook()
ws = wb.active
ws.title = '报告'

# 将数据添加到Excel工作表中
for row in data.iterrows():
    ws.append(row[1].tolist())

# 插入图表图片
img = Image('sales_chart.png')
ws.add_image(img, 'A10')

# 保存Excel报告
wb.save('report.xlsx')
