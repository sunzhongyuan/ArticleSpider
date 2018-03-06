# -*- coding: utf-8 -*-
import scrapy
import re
import json
import time
from PIL import Image
from urllib import parse
from scrapy.loader import ItemLoader
from items import ZhihuQuestionItem, ZhihuAnswerItem
import datetime


class ZhihuSpider(scrapy.Spider):
    name = 'zhihu'
    allowed_domains = ['www.zhihu.com']
    start_urls = ['http://www.zhihu.com/']

    agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36'
    header = {
        'HOST': 'www.zhihu.com',
        'Referer': 'https://www.zhihu.com',
        'User-Agent': agent
    }

    # 获取问题回答的url，第一个参数是问题的ID，第二个参数offset是从第几个获取，limit=20表示每次返回回答的个数，默认20
    answer_url = 'https://www.zhihu.com/api/v4/questions/{0}/answers?include=data%5B*%5D.is_normal%2Cadmin_closed_comment%2Creward_info%2Cis_collapsed%2Cannotation_action%2Cannotation_detail%2Ccollapse_reason%2Cis_sticky%2Ccollapsed_by%2Csuggest_edit%2Ccomment_count%2Ccan_comment%2Ccontent%2Ceditable_content%2Cvoteup_count%2Creshipment_settings%2Ccomment_permission%2Ccreated_time%2Cupdated_time%2Creview_info%2Crelevant_info%2Cquestion%2Cexcerpt%2Crelationship.is_authorized%2Cis_author%2Cvoting%2Cis_thanked%2Cis_nothelp%2Cupvoted_followees%3Bdata%5B*%5D.mark_infos%5B*%5D.url%3Bdata%5B*%5D.author.follower_count%2Cbadge%5B%3F(type%3Dbest_answerer)%5D.topics&offset={1}&limit=20&sort_by=default'

    # yield的request没有指定callback函数，默认调用这个函数
    def parse(self, response):
        # 深度优先爬取知乎
        # 这里从知乎主页获取所有URL链接，循环这些链接，判断链接格式，是question的进行question解析，
        # 不是question的循环调用本函数，继续判断url格式

        # 获取本页面所有的url
        all_urls = response.css('a::attr(href)').extract()
        # 拼接成完整url
        all_urls = [parse.urljoin(response.url, url) for url in all_urls]
        # 过滤URL
        all_urls = filter(lambda x: True if x.startswith('https') else False, all_urls)
        # 循环URL
        for url in all_urls:
            # 调试指定页面时可以指定url
            # url = 'https://www.zhihu.com/question/41363928'
            print(url)
            # 判断URL格式，是问题页面的，request获取这个页面，在parse_question函数中解析问题，存储到问题的item里
            match_obj = re.match('(.*zhihu.com/question/(\d+))', url)
            if match_obj:
                request_url = match_obj.group(1)
                question_id = match_obj.group(2)
                yield scrapy.Request(request_url, headers=self.header, meta={'question_id': question_id},
                                     callback=self.parse_question)
                # 调试时这里可以加一个break，这样只会下载一个问题页面进行处理，便于分析问题
                break
            # 不是问题的页面，下载回来继续执行本函数进行分析这个页面的URL，达到深度优先
            else:
                # yield scrapy.Request(url, headers=self.header, callback=self.parse)
                pass

    def parse_question(self, response):
        zhihu_id = response.meta.get('question_id', '')

        # 使用ItemLoader加载item
        item_loader = ItemLoader(ZhihuQuestionItem(), response=response)
        item_loader.add_value('zhihu_id', zhihu_id)
        item_loader.add_css('topics', '.QuestionHeader-topics .Popover div::text')
        item_loader.add_value('url', response.url)
        item_loader.add_css('title', '.QuestionHeader-title::text')
        item_loader.add_css('content', '.QuestionHeader-detail')
        # if 'answer' in response.url:
        #     item_loader.add_css('answer_num', '.Question-mainColumn a.QuestionMainAction::text')
        # else:
        #     item_loader.add_css('answer_num', '.QuestionAnswers-answers .List-headerText span::text')
        # 从两种不同的样式中获取数据 可以用xpath的 | 或符号
        item_loader.add_xpath('answer_num',
                              '//*[@class="List-headerText"]/span/text()|//a[@class="QuestionMainAction"]/text()')
        item_loader.add_css('comments_num', '.QuestionHeader-Comment button::text')
        item_loader.add_css('watch_user_num', '.QuestionFollowStatus .NumberBoard-itemValue::text')
        item_loader.add_css('click_num', '.QuestionFollowStatus .NumberBoard-itemValue::text')

        # 根据上面我们定义的规则将ItemLoader加载成question_item
        question_item = item_loader.load_item()

        # 如果这个问题有人回答，则发送请求获取回答信息
        # 没有回答将回答数赋值为0
        if 'answer_num' in question_item:
            # 问题页面有回答，我们拼接一个获取回答的请求，进行分析回答
            yield scrapy.Request(self.answer_url.format(zhihu_id, 0), headers=self.header, callback=self.parse_answer)
        else:
            question_item['answer_num'] = ['0']

        # 这里yield出去什么，scrapy会自动分析，如果是一个itme，会自动调用pipeline；如果是request会自动下载这个页面，跳转到callback函数
        yield question_item

    def parse_answer(self, response):
        # 回答请求返回的是json格式，可以load处理
        ans_json = json.loads(response.text)
        is_end = ans_json['paging']['is_end']
        next_url = ans_json['paging']['next']

        for answer in ans_json['data']:
            answer_item = ZhihuAnswerItem()
            answer_item['zhihu_id'] = answer['id']
            answer_item['url'] = answer['url']
            answer_item['question_id'] = answer['question']['id']
            answer_item['author_id'] = answer['author']['id'] if 'id' in answer['author'] else None
            answer_item['content'] = answer['content'] if 'content' in answer else answer['excerpt']
            answer_item['praise_num'] = answer['voteup_count']
            answer_item['comments_num'] = answer['comment_count']
            answer_item['create_time'] = answer['created_time']
            answer_item['update_time'] = answer['updated_time']
            # answer_item['crawl_time'] = datetime.datetime.now()
            answer_item['crawl_time'] = time.time()

            yield answer_item

        # 判断是否结束，如果没有结束进行请求next_url，next_url是json返回的
        if not is_end:
            yield scrapy.Request(next_url, headers=self.header, callback=self.parse_answer)

    # start_requests是spider的入口函数，循环发送start_urls数组里的url
    # 这里重写这个函数，实现登陆知乎的操作，登陆之后才能爬取知乎的内容
    # 这个函数需要返回一个数组，scrapy的代码这里需要一个可迭代的，具体没研究
    def start_requests(self):
        # 第一步需要登陆，登陆需要获取xsrf，获取xsrf可以像zhihu_login_requests.py里的get_xsrf函数那样获取
        # 也可以用scrapy异步请求一个URL，获得页面的response，然后回调一个函数，在那个函数里通过正则获取到xsrf

        # 以下yield return都可以 有什么区别呢
        # 初步猜测：yield多应用于循环中，循环请求一个数组中的多个url，处理完一个url后继续回到这里再发送下一个请求
        #          return就直接提交里，这个函数就结束了
        # return [scrapy.Request('https://www.zhihu.com/#signin', callback=self.login, headers=self.header)]
        # yield scrapy.Request('https://www.zhihu.com/#signin', callback=self.login, headers=self.header)

        # 新版去掉xsrf
        return [scrapy.Request('https://www.zhihu.com/explore', callback=self.login, headers=self.header)]

    def login(self, response):
        match_obj = re.search('.*xsrf.*value="(.*?)"', response.text)
        if match_obj:
            xsrf = match_obj.group(1)
        else:
            xsrf = '新版去掉xsrf'
        if xsrf:
            post_url = "https://www.zhihu.com/login/phone_num"
            post_data = {
                # '_xsrf': xsrf,
                'phone_num': '15522523676',
                'password': 'sun112788',
                'remember_me': 'true'
            }

            # 获取验证码
            # 获取验证码图片我们需要发送一个请求，直接发送请求会导致这个请求和当前请求不在同一会话内
            # 这里用yield是为了保证验证码和登陆在一个会话内，scrapy中yield会保证在同一个会话内操作，利用callback函数衔接
            t = str(int(time.time() * 1000))
            captcha_url = 'https://www.zhihu.com/captcha.gif?r={0}&type=login'.format(t)
            yield scrapy.Request(url=captcha_url, headers=self.header,
                                 meta={'post_data': post_data, 'post_url': post_url}, callback=self.login_after_captcha)

    # 识别验证码请求返回的验证码图片中的验证码，将验证码加入的请求登陆的表单中，提交表单登陆
    def login_after_captcha(self, response):
        with open('captcha.jpg', 'wb') as f:
            f.write(response.body)

        # 显示图片
        im = Image.open('captcha.jpg')
        im.show()
        im.close()

        # 在console输入图片中的验证码
        captcha = input('输入验证码\n>')

        post_url = response.meta.get('post_url', '')
        post_data = response.meta.get('post_data', {})
        post_data['captcha'] = captcha
        # FormRequest可以提供form表单的提交
        # 这里再提交一个form表单的请求，看看知乎给返回什么
        # 我们提交的登陆请求，获取response，在callback函数里判断是否登陆成功
        # 登陆成功就可以继续执行start_requests本来需要执行的代码
        return [scrapy.FormRequest(
            url=post_url,
            formdata=post_data,
            headers=self.header,
            callback=self.check_login
        )]

    # 验证是否登陆成功
    def check_login(self, response):
        text_json = json.loads(response.text)
        print(text_json)
        if 'msg' in text_json and text_json['msg'] == '登录成功':
            for url in self.start_urls:
                # scrapy的所有请求如果不指定callback函数，则默认调用parse函数，默认的
                yield scrapy.Request(url, dont_filter=True, headers=self.header)


