# -*- coding: utf-8 -*-
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from scrapy.loader import ItemLoader
from items import LagouJobItem, LagouJobItemLoader
from utils.common import get_md5
import datetime


class LagouSpider(CrawlSpider):
    name = 'lagou'
    allowed_domains = ['www.lagou.com']
    start_urls = ['https://www.lagou.com/']

    '''
        CrawlSpider基于Spider，相比普通的Spider它可以智能提取页面中的所有的链接，并且下载这些页面，供我们解析处理
            我们只需要写一个规则，说明什么样的链接做什么样的处理就可以了，
            在规则中我们可以指定某个callback函数对某一类链接对处理，不指定callback函数默认操作是提取当前页面对链接并下载
            当然是否提取链接还是由规则中的follow参数决定，True就提取，False不提取
            没有指定follow参数时，follow参数的默认值由是否指定callback函数决定，
                有callback就False，无callback就True（源码这么写的：self.follow = False if callback else True）
        关于的CrawlSpider流程：
            1。还是先执行start_requests对start_urls里对每一个URL发起请求
            2。请求回来的response被默认的parse方法接收处理，parse方法CrawlSpider已经定义好了，我们不可以重写覆盖
            3。定义好的parse做了如下处理：
                return self._parse_response(response, self.parse_start_url, cb_kwargs={}, follow=True)
                调用了CrawlSpider的一个核心方法_parse_response，其中参数parse_start_url是一个callback函数，它是CrawlSpider预先定义的一个空方法
                我们可以重写这个方法来处理response，也可以不重写继续执行CrawlSpider为我们提供的功能
                _parse_response方法是CrawlSpider的核心，会被多次调用，这里只是为了代码复用而调用了一次
            4。_parse_response方法：def _parse_response(self, response, callback, cb_kwargs, follow=True):
                a。先判断是否有callback函数，没有则跳过这步
                    调用callback方法处理response，处理的结果再传到process_results方法进一步处理
                    process_results是CrawlSpider提供的一个空方法，我们可以根据自己的需求决定是否重写这个方法
                b。判断是否继续从response里提取url，
                    是否提取由两个参数共同决定，一个是传入的follow参数，另一个是setting文件中CRAWLSPIDER_FOLLOW_LINKS的值，True or False，
                    调用_requests_to_follow方法做后续提取等主要操作
            5。_requests_to_follow方法：def _requests_to_follow(self, response):
                这个方法里就用到了我们自定义的提取url的规则
                规则如何定义：
                    通过定义CrawlSpider对象的rules属性，它是规则类Rule的一个集合，可以写多个Rule类放在里面，一个Rule就是一个规则
                    rules = (
                        Rule(LinkExtractor(allow='zhaopin/.*'), follow=True),
                        Rule(LinkExtractor(allow='jobs/\d+.html'), callback='parse_job', follow=True),
                    )
                    Rule类有这些参数（link_extractor, callback=None, cb_kwargs=None, follow=None, process_links=None, process_request=identity）
                        link_extractor：是一个LinkExtractor类，它定义了需要提取的URL的规则
                            LinkExtractor类有这些参数（allow=(), deny=(), allow_domains=(), deny_domains=(), restrict_xpaths=(), tags=('a', 'area'), attrs=('href',), canonicalize=False, unique=True, process_value=None, deny_extensions=None, restrict_css=(), strip=True）
                                很多参数，但是大部分不需要我们指定，都默认即可，这里说明几个常用参数：
                                allow：这个是正则表达式字符串，也可以是正则表达式字符串的元祖，满足的值会被提取，如果为空，则全部匹配。
                                deny：与allow相反，满足的不会被提取
                                allow_domains：会被提取的链接的domains
                                deny_domains：一定不会被提取链接的domains
                                restrict_xpaths：使用xpath表达式，和allow共同作用过滤链接，比如只提取正文内的链接，可以在这里选择正文部分
                                restrict_css：使用css选择器，和restrict_xpaths作用一样
                        callback：符合规则的页面下载回来后用哪个函数处理，不传不处理，这里需要传字符串
                        cb_kwargs：自定义的参数，会作为参数传入到callback函数里
                        follow：是否继续获取当前页面的链接
                            上面这三个参数后续会作为参数传入_parse_response函数处理
                        process_links：需要传入一个自定义方法的名称的字符串，在_requests_to_follow方法中被调用，发送请求之前调用，多用于URL的再加工
                        process_request：需要传入一个自定义方法名称的字符串，根据url创建request类后，这个request会作为参数传入这个方法，多用来处理request类
                            注意callback，process_links，process_request这三个参数需要传入方法名称的字符串，
                            不能传入方法名称，CrawlSpider在初始化时会调用_compile_rules方法，这个方法将rules浅拷贝为_rules，同时将这三个字符串转换为方法，具体怎么转的看源码
                以上就是关于规则的定义方法，以及CrawlSpider如何获取这些rules
                process_request会逐个处理这些Rule
                a。首先根据LinkExtractor类定义的URL规则提取出页面中的URL
                b。然后有一个去重操作，对当前页面的URL进行去重
                c。如果自定义了process_links方法，则调用process_links方法处理url
                d。接着调用_build_request方法，这个方法用来构建一个request，并返回这个request
                e。返回的request会被process_request函数处理，如果定义了process_request函数的话
                f。process_request函数必须返回一个request或None
                g。最后本方法yield出去这个request或者None，yield出去这个request的callback是_response_downloaded方法
                h。_response_downloaded方法
                    会将这个response和rule规则里的callback、cb_kwargs、follow这个四个作为参数调用_parse_response方法
                i。又回到了_parse_response方法
        
        总结一下可以让我重构的方法：
            parse_start_url
            process_results
            process_links
            process_request
    '''

    # 这个是spider类的一个属性，可以自定义setting文件的配置，也可以在setting文件里直接配置
    custom_settings = {
        "COOKIES_ENABLED": False,
        "DOWNLOAD_DELAY": 1,
        # 'DEFAULT_REQUEST_HEADERS': {
            # 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36'
        # }
    }

    rules = (
        # Rule(LinkExtractor(allow='zhaopin/.*'), follow=True),
        # Rule(LinkExtractor(allow='gongsi/.*'), follow=True),
        Rule(LinkExtractor(allow='jobs/\d+.html'), callback='parse_job', follow=True),
    )

    def parse_job(self, response):
        item_loader = LagouJobItemLoader(LagouJobItem(), response)
        item_loader.add_value('url', response.url)
        item_loader.add_value('url_object_url', get_md5(response.url))
        item_loader.add_css('title', '.job-name::attr(title)')
        item_loader.add_css('salary', '.job_request span.salary::text')
        item_loader.add_css('job_city', '.job_request span:nth-child(2)::text')
        # xpath选择第二个这么写
        # item_loader.add_xpath('job_city', '//*[@class="job_request"]/p/span[2]/text()')
        item_loader.add_css('work_year', '.job_request span:nth-child(3)::text')
        item_loader.add_css('degree_need', '.job_request span:nth-child(4)::text')
        item_loader.add_css('job_type', '.job_request span:nth-child(5)::text')
        item_loader.add_css('publish_time', '.publish_time::text')
        item_loader.add_css('tags', '.position-label li::text')
        item_loader.add_css('job_advantage', '.job-advantage p::text')
        item_loader.add_css('job_desc', '.job_bt div')
        item_loader.add_css('job_addr', '.work_addr a:not(#mapPreview)::text, .work_addr::text')
        # item_loader.add_css('job_addr', '.work_addr')
        item_loader.add_css('company_url', '.job_company dt a::attr(href)')
        item_loader.add_css('company_name', '.job_company dt a img::attr(alt)')
        item_loader.add_value('crawl_time', datetime.datetime.now())

        job_item = item_loader.load_item()
        return job_item
