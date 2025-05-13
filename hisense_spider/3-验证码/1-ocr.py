#!/user/bin/env python
# -*-coding:utf-8-*-
from PIL import Image
import pytesseract

if __name__ == '__main__':
    # 打开图片
    for i in range(50):

        image = Image.open(f"./xlj/{i}.jpg")

        # # 将彩色图片转换为灰度图片
        img = image.convert('L')

        # t = 155  # 设置阈值
        # table = []
        # for i in range(256):
        #     if i < t:
        #         table.append(0)
        #     else:
        #         table.append(1)
        # # 将图片进行二进制化处理
        # img = img.point(table, '1')
        # img.save('code4.png')
        # img.show() ## 显示处理后图片



        # 识别图片中的文字
        # text = pytesseract.image_to_string(img, 'chi_sim', config='-c tessedit_char_whitelist=0123456789')
        text = pytesseract.image_to_string(img, 'chi_sim')

        print("识别结果：", text)
