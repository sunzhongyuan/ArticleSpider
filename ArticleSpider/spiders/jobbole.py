# -*- coding: utf-8 -*-
import scrapy
import re
import datetime
from scrapy.http import Request     # 用于发送请求
from urllib import parse    # parse.urljoin(response.url, post_url) 用于拼接URL,如果post_url没有域名，则提取response.url的URL
from ArticleSpider.items import JobBoleArticleItem, ArticleItemLoader   # ArticleItemLoader为重载的ItemLoader，自定义类output_processor
from ArticleSpider.utils import common
from scrapy.loader import ItemLoader    # ItemLoader是scrapy提供的加载item的模块，ItemLoader可以自定义一些规则，然后根据这些规则解析生成item


class JobboleSpider(scrapy.Spider):
    name = 'jobbole'
    allowed_domains = ['blog.jobbole.com']
    start_urls = ['http://blog.jobbole.com/all-posts/']     # 所有文章页面作为入口页面

    def parse(self, response):
        """
            这个函数是由start_requests函数调起的，start_requests是spider的入口函数
            start_requests函数会逐条发送start_urls这个数组里的url请求，默认的callback函数就是这个parse函数
            response是请求返回的内容
        :param response:
        :return:
        """

        # 已经获取到了全部文章页面的response，我们从这个页面解析出所有具体文章的链接，
        # 再发送这个链接请求，就可以获取到文章页面的response，
        # 从文章页面的response就可以解析出文章相关内容，然后保存到数据库

        # css选择器，一层一层的获取，从前往后，最外层到最内层具体要爬取的内容
        # #archive          id为archive的div
        # .floated-thumb    class包含floated-thumb的div
        # .post-thumb       class包含post-thumb的div
        # a                 所有的a标签
        # 获取到这里没有进行extract啥也看不出来，不进行extract是因为既要提取出当前层a的链接地址，还要提取出下一层的img的src
        post_nodes = response.css("#archive .floated-thumb .post-thumb a")
        for post_node in post_nodes:
            # 逐条再次解析
            # 获取下层img标签的src属性值
            img_url = post_node.css('img::attr(src)').extract_first('')
            # 获取当前层a标签的href属性值
            post_url = post_node.css('::attr(href)').extract_first('')
            # 想要爬取的文件链接取出来来，下面异步请求这个页面，返回的内容response在callback函数内爬取并存储到数据库
            # 参数说明： url是发送的请求；
            #               parse.urljoin这个函数可以智能拼接URL
            #               如获取到的文章链接是/113367/，调用这个函数会将两个url拼接在一起，变成http://blog.jobbole.com/113367/
            #               如获取到的文章链接是http://blog.jobbole.com/113367/，就不会拼接了
            #           callback是处理这个请求的函数名，异步处理的；
            #           meta是我们自定义的加到request里的字段，在处理函数中从response中获取，meta是个字典
            yield Request(url=parse.urljoin(response.url, post_url), meta={'front_image_url': img_url},
                          callback=self.parse_detail)

        # 提取下一页URL
        # 当前页能提取到的文章url都爬取完了之后，需要爬取下一页的文章url
        # 这里我们需要模拟点击下一页，也就是发送一个下一页链接请求，将点击后返回的response交给callback函数处理，
        # 这个的callback函数是当前函数，也就是一个循环，直到无法获取下一页的url为止
        next_urls = response.css('.next.page-numbers::attr(href)').extract_first('')
        if next_urls:
            yield Request(url=parse.urljoin(response.url, next_urls), callback=self.parse)

    def parse_detail(self, response):
        """
            这个函数用来解析具体的文章页，response就是点击文章链接后返回的文章页面内容，我们需要处理的
        """

        # 提取的内容需要存放到数据库，这个对象是和数据库表对应的一个对象，scrapy叫它item
        article_item = JobBoleArticleItem()

        # ———————————第一种生成item的方法：逐个获取，然后处理数据，最后放在item里（item因为第二种方法已经改动了）———————————————

        # 获取自定义的字段，从meta中获取
        front_image_url = response.meta.get('front_image_url', '')

        # 使用xpath获取字段
        # title = response.xpath('//*[@id="post-112886"]/div[1]/h1/text()').extract()[0]
        # vote = int(response.xpath('//span[contains(@class, "vote-post-up")]/h10/text()').extract()[0])

        # 使用css选择器提取字段

        # 获取标题
        title2 = response.css('div.entry-header > h1::text').extract_first('')

        # 获取创建日期
        create_date = response.css('p.entry-meta-hide-on-mobile::text').extract()[0].strip().replace('·', '').strip()

        # 获取点赞数
        praise_nums = int(response.css('span.vote-post-up > h10::text').extract()[0])

        # 获取收藏数
        fav_nums = response.css('span.bookmark-btn::text').extract()[0].strip()
        match_re = re.match('.*?(\d+).*', fav_nums)
        if match_re:
            fav_nums = int(match_re.group(1))
        else:
            fav_nums = 0

        # 获取评论数
        comment_nums = response.css('a[href="#article-comment"] > span::text').extract()[0].strip()
        match_re = re.match('.*?(\d+).*', comment_nums)
        if match_re:
            comment_nums = int(match_re.group(1))
        else:
            comment_nums = 0

        # 获取文章内容
        content = response.css('div.entry').extract()[0]

        # 获取标签
        tags = response.css('p.entry-meta-hide-on-mobile a::text').extract()
        tag_list = [tag for tag in tags if not tag.strip().endswith('评论')]
        tags = ','.join(tag_list)

        article_item['title'] = title2
        try:
            create_date = datetime.datetime.strptime(create_date, '%Y/%m/%d').date()
        except Exception as e:
            create_date = datetime.datetime.now().date()
        article_item['create_date'] = create_date
        article_item['url'] = response.url
        article_item['url_object_id'] = common.get_md5(response.url)
        article_item['front_image_url'] = [front_image_url]
        article_item['praise_nums'] = praise_nums
        article_item['comment_nums'] = comment_nums
        article_item['fav_nums'] = fav_nums
        article_item['tags'] = tags
        article_item['content'] = content

        # ——————————————————————————————————————————————————————————————————————————————————————————————————————————————
        # ———————第二种加载item的方法：通过itemloader加载item，好处是数据的处理统一放到了item类中去处理，减少代码量，增强可读性————
        # ——————————————————————————————————————————————————————————————————————————————————————————————————————————————
        '''
        思路：
        1,创建一个ItemLoad对象    
        2,通过该对象的add_css或者add_xpath或者add_value方法将解析语句装入ItemLoader
        3,在Item.py中在Filder()中调用函数，用来清洗，处理数据
        4,artical_item = item_loader.load_item() 调用这个对象的此方法，写入到Item中
        '''
        # item_loader = ItemLoader(item=JobBoleArticleItem(), response=response)
        item_loader = ArticleItemLoader(item=JobBoleArticleItem(), response=response)  # 自定义的itemloader
        '''
        ItemLoader重要的方法有下面这三个
        item_loader.add_css()
        item_loader.add_xpath()
        item_loader.add_value()
        '''
        item_loader.add_css('title', 'div.entry-header > h1::text')
        item_loader.add_css('create_date', 'p.entry-meta-hide-on-mobile::text')
        item_loader.add_value('url', response.url)
        item_loader.add_value('url_object_id', common.get_md5(response.url))
        item_loader.add_value('front_image_url', [front_image_url])
        item_loader.add_css('praise_nums', 'span.vote-post-up > h10::text')
        item_loader.add_css('comment_nums', 'a[href="#article-comment"] > span::text')
        item_loader.add_css('fav_nums', 'span.bookmark-btn::text')
        item_loader.add_css('tags', 'p.entry-meta-hide-on-mobile a::text')
        item_loader.add_css('content', 'div.entry')

        # 添加以上这些规则后需要调用一个load_item方法，将这些规则解析成item
        article_item = item_loader.load_item()

        yield article_item


