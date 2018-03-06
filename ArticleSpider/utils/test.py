# -*- coding: utf-8 -*-
__author__ = 'zyzy'

import urllib.request
import http.cookiejar

url = 'http://www.baidu.com'
url = 'http://fanyi.baidu.com/translate#en/zh/GitHub%20is%20home%20to%20over%2020%20million%20developers%20working%20together%20to%20host%20and%20review%20code%2C%20manage%20projects%2C%20and%20build%20software%20together.'

# 直接通过url来获取网页数据
print('第一种')
response = urllib.request.urlopen(url)
code = response.getcode()
html = response.read()
mystr = html.decode("utf8")
response.close()
print(mystr)
with open('bbbb.html', 'w') as w:
    w.write(mystr)

# 构建request对象进行网页数据获取
print('第二种')
request2 = urllib.request.Request(url)
request2.add_header('user-agent', 'Mozilla/5.0')
response2 = urllib.request.urlopen(request2)
html2 = response2.read()
mystr2 = html2.decode("utf8")
response2.close()
print(mystr2)

# 使用cookies来获取
print('第三种')
cj = http.cookiejar.LWPCookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
urllib.request.install_opener(opener)
response3 = urllib.request.urlopen(url)
print(cj)
html3 = response3.read()
mystr3 = html3.decode("utf8")
response3.close()
print(mystr3)