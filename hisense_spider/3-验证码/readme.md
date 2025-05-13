### 自动识别验证码
##### tesseract
> tesseract下载地址：https://digi.bib.uni-mannheim.de/tesseract/  
> 配置环境变量
为了在全局使用方便，比如安装路径为E:\work\myWork\tools-installation\Tesseract-OCR，将该路径添加
到环境变量的path中    
> 配置完成后在命令行输入tesseract -v，如果出现如下图所示，说明环境变量配置成功  

```
4、安装其他模块
pip install pytesseract
pip install pillow
```

demo

```
from PIL import Image
import pytesseract

im = Image.open('111.jpg')

# 识别文字，并指定语言
string = pytesseract.image_to_string(im, lang='chi_sim')
print(string)
```
