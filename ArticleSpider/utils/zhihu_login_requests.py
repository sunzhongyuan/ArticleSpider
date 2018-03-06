# -*- coding: utf-8 -*-
__author__ = 'zyzy'

'''
    requests模拟登陆知乎，包括使用cookie自动登陆
'''

import requests     # requsets模块 发送请求 可百度requests文档学习
try:
    import cookielib    # python2   cookielib相关模块
except:
    import http.cookiejar as cookielib  # python3   这样写可以实现python2和python3兼容
import re
import shutil   #
import time     # 时间模块，这里用于生成随机数
from PIL import Image   # 这里用来打开图片


# 会话对象，能够跨请求保持某些参数，它也会在同一个 Session 实例发出的所有请求之间保持cookie
session = requests.session()


# LWPCookieJar是python中管理cookie的工具，可以将cookie保存到文件，或者在文件中读取cookie数据到程序
session.cookies = cookielib.LWPCookieJar(filename='cookies.txt')    # 调用这个的save方法可以将cookie存储到filename的文件中
try:
    session.cookies.load(ignore_discard=True)   # 调用load读取cookie文件，ignore_discard=True忽略关闭浏览器丢失，ignore_expires=True忽略失效
except:
    print('cookie未能加载')


# 这里要自己定义一个请求的header，默认的是python的header，网站服务器会筛选是哪里发来的请求，这里模仿浏览器发送的请求
# agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_2) AppleWebKit/604.4.7 (KHTML, like Gecko) Version/11.0.2 Safari/604.4.7'
agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36'
header = {
    'HOST': 'www.zhihu.com',
    'Referer': 'https://www.zhihu.com',
    'User-Agent': agent
}


# 获取_xsrf，xsrf是服务器生成的，传递给浏览器，浏览器发送特定请求需要带着xsrf才可以请求成功，这个xsrf可以在html中隐藏域中获取
def get_xsrf():
    response = session.get('https://www.zhihu.com', headers=header)    # 这里注意headers参数，我们要自定义header，模拟浏览器
    # response.text 是服务器返回的html页面，其中就有xsrf，<input type="hidden" name="_xsrf" value="5903a96c29735c6a0eb8e3bd99d15ee0"/>
    # 我们可以用正则将xsrf匹配出来，因为match只能匹配单行，有换行符就无法成功匹配，所以这里用search
    # 也可以用match，match有一个参数re.DOTALL(或re.S)使得 . 匹配包括换行符在内的任意字符
    match_obj = re.search('.*xsrf.*value="(.*?)"', response.text)
    if match_obj:
        print(match_obj.group(1))
        return match_obj.group(1)
    else:
        return ''


# 验证码模块，获取验证码图片
def get_captcha():
    t = str(int(time.time()*1000))
    captcha_url = 'https://www.zhihu.com/captcha.gif?r={0}&type=login'.format(t)
    # 这里要用session请求，session会保存cookie，保证验证码是当前登陆会话的，
    # 不能用request，request请求回来的是不同会话的，验证码无法校验成功
    t = session.get(captcha_url, headers=header)
    with open('captcha.jpg', 'wb') as f:
        f.write(t.content)

    # 显示图片
    im = Image.open('captcha.jpg')
    im.show()
    im.close()

    # 在console输入图片中的验证码
    captcha = input('输入验证码\n')
    return captcha


def zhihu_login(account, password):
    if re.match('^1\d{10}', account):
        print('手机号码登陆')
        post_url = "https://www.zhihu.com/login/phone_num"
        post_data = {
            '_xsrf': get_xsrf(),
            'phone_num': account,
            'password': password,
            'captcha': get_captcha()
            # 'captcha_type': 'cn'
        }
    elif '@' in account:
        print('邮箱登陆')
        post_url = "https://www.zhihu.com/login/email"
        post_data = {
            '_xsrf': get_xsrf(),
            'email': account,
            'password': password
            # 'captcha_type': 'cn'
        }
    response_text = session.post(post_url, post_data, headers=header)
    print(response_text.text)
    session.cookies.save()  # 保存cookie信息到本地


# 获取主页
def get_index():
    response = session.get('https://www.zhihu.com', headers=header)
    with open('index_page.html', 'wb') as f:
        f.write(response.text.encode('utf-8'))
    print('ok')


# 判断是否登陆
def is_login():
    inbox_url = 'https://www.zhihu.com/inbox'   # 私信页面
    # allow_redirects=False是否重定向为False，否则302会重定向到登陆界面，返回码变成200，无法判断是否是登陆状态
    response = session.get(inbox_url, headers=header, allow_redirects=False)
    if response.status_code != 200:
        print('未登录')
        return False
    else:
        print('已登录')
        return True


zhihu_login('15522523676', 'sun112788')
# get_index()
# is_login()
# get_xsrf()
# get_captcha()
