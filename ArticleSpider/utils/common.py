# -*- coding: utf-8 -*-
__author__ = 'zyzy'
import hashlib
import re


def get_md5(url):
    if isinstance(url, str):    # 无法转换unicode编码，如果是unicode需要转换一下编码才能做md5
        url = url.encode('utf-8')
    m = hashlib.md5()
    m.update(url)
    return m.hexdigest()


def extract_num(text):
    match_re = re.match('.*?(\d+).*', text)
    if match_re:
        nums = int(match_re.group(1))
    else:
        nums = 0
    return nums


if __name__ == '__main__':  # 测试用，直接执行这个文件即可
    print(get_md5('http://baidu.com'))


