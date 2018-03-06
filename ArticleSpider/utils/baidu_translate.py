# -*- coding: utf-8 -*-
__author__ = 'zyzy'
import requests
import json
import sys
import os.path
import time


class BaiduTranslate:
    def __init__(self, query, outfile=None, type='f'):
        self.query = query
        self.outfile = outfile
        self.type = type
        self.url = 'http://fanyi.baidu.com/v2transapi'
        self.url_bing = 'https://www.bing.com/translator/api/Dictionary/Lookup?from=en&to=zh-CHS'
        self.url_bing = 'https://www.bing.com/translator/api/Translate/TranslateArray?from=-&to=zh-CHS'
        self.header = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_2) AppleWebKit/604.4.7 (KHTML, like Gecko)'
                          ' Version/11.0.2 Safari/604.4.7'
        }
        self.header_bing = {
            'Referer': 'https://www.bing.com/translator/',
            'Content-Type': 'application/json;charset=UTF-8',
            'Origin': 'https://www.bing.com',
            'Host': 'www.bing.com',
            'Accept': 'application/json,text/javascript,*/*;q=0.01',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_2) AppleWebKit/604.4.7 (KHTML, like Gecko)'
                          ' Version/11.0.2 Safari/604.4.7'
        }
        self.post_date = {
            'from': 'en',
            'to': 'zh',
            'query': 'test',
            'transtype': 'translang',
            'simple_means_flag': '3'
        }
        self.post_date_bing = {
            "from": "en",
            "to": "zh-CHS",
        }
        self.post_json_bing = json.dumps({
            "from": "en",
            "to": "zh-CHS",
            "items": [
                {
                    # "id": str(int(time.time() * 1000))[10:0:-1],
                    "id": '112785',
                    "text": "red",
                    "wordAlignment": ""
                }
            ]
        })

    def run(self):
        if self.outfile:
            with open(self.outfile, 'w')as w:
                if os.path.isfile(self.query) and self.type == 'f':
                    with open(self.query, 'r') as f:
                        while True:
                            query = f.readline()
                            if query:
                                w.write(self.translate(query) + '\n')
                            else:
                                break
                else:
                    w.write(self.translate(self.query))
            return self.outfile
        else:
            result = ''
            if os.path.exists(self.query) and self.type == 'f':
                with open(self.query, 'r') as f:
                    while True:
                        query = f.readline()
                        if query:
                            result = result + self.translate(query) + '\n'
                        else:
                            break
            else:
                result = self.translate(self.query)
            return result

    def translate(self, query):
        if self.check_cn(query):
            self.post_date['from'] = 'zh'
            self.post_date['to'] = 'en'
        else:
            self.post_date['from'] = 'en'
            self.post_date['to'] = 'zh'
        self.post_date['query'] = query
        response = requests.post(self.url, self.post_date, headers=self.header)
        response = response.content.decode()
        dict_response = json.loads(response)
        return dict_response['trans_result']['data'][0]['dst']

    def translate_bing(self, query):
        if self.check_cn(query):
            self.post_date_bing['from'] = 'zh-CHS'
            self.post_date_bing['to'] = 'en'
            self.url_bing = self.url_bing + 'en'
        else:
            self.post_date_bing['from'] = 'en'
            self.post_date_bing['to'] = 'zh-CHS'
            self.url_bing = self.url_bing + 'zh-CHS'
        # self.post_date_bing['items'][0]['text'] = query
        response = requests.post(self.url_bing, self.post_date_bing, self.post_json_bing, headers=self.header)
        response = response.content.decode()
        dict_response = json.loads(response)
        return dict_response['trans_result']['data'][0]['dst']

    def check_cn(self, str):
        for ch in str:
            if u'\u4e00' <= ch <= u'\u9fff':
                return True
        return False


if __name__ == '__main__':
    # print(BaiduTranslate('red', None).run())
    try:
        query = sys.argv[1]
    except:
        print('请输入要翻译的内容或文件')
        exit()
    try:
        outfile = sys.argv[2]
        if not outfile.endswith('.txt'):
            outfile = None
    except:
        outfile = None

    print(BaiduTranslate(query, outfile).run())

