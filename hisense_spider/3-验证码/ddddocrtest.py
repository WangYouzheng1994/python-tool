#!/user/bin/env python
# -*-coding:utf-8-*-
import ddddocr

if __name__ == '__main__':
    ocr = ddddocr.DdddOcr()
    with open('./xlj/1.jpg', 'rb') as f:
        img_bytes = f.read()
        res = ocr.classification(img_bytes)
        print(res)