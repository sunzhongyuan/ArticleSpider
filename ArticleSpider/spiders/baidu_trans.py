# -*- coding: utf-8 -*-
import scrapy


class BaiduTransSpider(scrapy.Spider):
    name = 'baidu_trans'
    allowed_domains = ['http://fanyi.baidu.com']
    start_urls = ['http://fanyi.baidu.com']

    agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36'
    header = {
        'Host': 'fanyi.baidu.com',
        'Referer': 'http://fanyi.baidu.com/translate',
        'User-Agent': agent
    }

    def parse(self, response):
        with open('aaa.html', 'wb') as w:
            w.write(response.text.encode('utf-8'))
        post_data = {
            'from': 'en',
            'to': 'zh',
            'query': 'GitHub test',
            'transtype': 'translang',
            'simple_means_flag': '3'
        }
        return [scrapy.FormRequest(
            url='http://fanyi.baidu.com/translate#en/zh/GitHub%20test',
            formdata=post_data,
            headers=self.header,
            callback=self.to_file
        )]

    def to_file(self, response):
        print(response.text)
        with open('bbb.html', 'wb') as w:
            w.write(response.text.encode('utf-8'))
