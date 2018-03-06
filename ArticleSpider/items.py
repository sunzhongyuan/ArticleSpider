# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy.loader.processors import MapCompose   # scrapy默认提供的input_processor，可以传递任意多的函数作为参数
from scrapy.loader.processors import TakeFirst    # scrapy提供的函数，作用是取数组的第一个
from scrapy.loader.processors import Join    # scrapy提供的函数，作用是将数组按照分隔符拼接成一个字符串
from scrapy.loader import ItemLoader    # 可以重载这个类，自定义output_processor
import datetime
import time
import re
from ArticleSpider.utils.common import extract_num  # 公共的从字符串中提取数字
from ArticleSpider.settings import SQL_DATE_FORMAT, SQL_DATETIME_FORMAT     # 自定义的日期格式，用于格式化日期
from w3lib.html import remove_tags


class ArticlespiderItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


# 演示用
def add_name(value):
    return value + '-zyzy'


# 将字符串转换为时间类型
def date_convert(value):
    try:
        create_date = datetime.datetime.strptime(value, '%Y/%m/%d').date()
    except Exception as e:
        create_date = datetime.datetime.now().date()
    return create_date


# 从字符串中获取数字
def get_nums(value):
    match_re = re.match('.*?(\d+).*', value)
    if match_re:
        nums = int(match_re.group(1))
    else:
        nums = 0
    return nums


# 去掉不符合规则的value，数组中每个值进行处理
def remove_comment_tags(value):
    if '评论' in value:
        return ''
    else:
        return value


# 空方法，用于覆盖默认的output_processor的方法
def return_value(value):
    return value


# 重载ItemLoader
class ArticleItemLoader(ItemLoader):
    default_output_processor = TakeFirst()


class JobBoleArticleItem(scrapy.Item):
    title = scrapy.Field(
        # 有两个参数，input_processor：当值传递进来当时候可以进行预处理；output_processor:当值传出时调用
        input_processor=MapCompose(lambda x: x+'-jobbole', add_name)
    )
    create_date = scrapy.Field(
        input_processor=MapCompose(date_convert)
    )
    url = scrapy.Field()
    url_object_id = scrapy.Field()
    front_image_url = scrapy.Field(
        output_processor=MapCompose(return_value)   # front_image_url需要下载图片的URL，需要一个数组类型
    )
    front_image_path = scrapy.Field()
    praise_nums = scrapy.Field(
        input_processor=MapCompose(get_nums)
    )
    comment_nums = scrapy.Field(
        input_processor=MapCompose(get_nums)
    )
    fav_nums = scrapy.Field(
        input_processor=MapCompose(get_nums)
    )
    tags = scrapy.Field(
        input_processor=MapCompose(remove_comment_tags),
        output_processor=Join(',')
    )
    content = scrapy.Field()

    def get_insert_sql(self):
        insert_sql = '''
            insert into article(title, url, url_object_id, create_date, fav_nums)
                            values (%s, %s, %s, %s, %s)
        '''
        params = (self['title'], self['url'], self['url_object_id'], self['create_date'], self['fav_nums'])

        return insert_sql, params


class ZhihuQuestionItem(scrapy.Item):
    zhihu_id = scrapy.Field()
    topics = scrapy.Field()
    url = scrapy.Field()
    title = scrapy.Field()
    content = scrapy.Field()
    answer_num = scrapy.Field()
    comments_num = scrapy.Field()
    watch_user_num = scrapy.Field()
    click_num = scrapy.Field()
    crawl_time = scrapy.Field()

    def get_insert_sql(self):
        insert_sql = '''
            insert into zhihu_question(zhihu_id, topics, url, title, content, answer_num, comments_num, watch_user_num, 
            click_num, crawl_time) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) 
            on duplicate key UPDATE content=VALUES(content), answer_num=VALUES(answer_num), 
            comments_num=VALUES(comments_num), watch_user_num=VALUES(watch_user_num), click_num=VALUES(click_num),
            crawl_update_time=VALUES(crawl_time)
        '''

        # 这个item是用ItemLoader加载的item，每一项都是list，可以像JobBoleArticleItem那样处理
        # 也可以自己手动处理
        zhihu_id = self['zhihu_id'][0]
        topics = ','.join(self['topics'])
        url = self['url'][0]
        title = self['title'][0]
        content = self['content'][0]
        answer_num = extract_num((''.join(self['answer_num']).replace(',', '')))
        comments_num = extract_num((''.join(self['comments_num']).replace(',', '')))
        watch_user_num = extract_num(self['watch_user_num'][0].replace(',', ''))
        click_num = extract_num(self['click_num'][1].replace(',', ''))
        crawl_time = datetime.datetime.now().strftime(SQL_DATETIME_FORMAT)

        params = (zhihu_id, topics, url, title, content, answer_num, comments_num, watch_user_num,
                  click_num, crawl_time)

        return insert_sql, params


class ZhihuAnswerItem(scrapy.Item):
    zhihu_id = scrapy.Field()
    url = scrapy.Field()
    question_id = scrapy.Field()
    author_id = scrapy.Field()
    content = scrapy.Field()
    praise_num = scrapy.Field()
    comments_num = scrapy.Field()
    create_time = scrapy.Field()
    update_time = scrapy.Field()
    crawl_time = scrapy.Field()

    def get_insert_sql(self):
        insert_sql = '''
            insert into zhihu_answer(zhihuid, url, question_id, author_id, content, praise_num, comments_num, 
            create_time, update_time, crawl_time) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            on duplicate KEY UPDATE content=VALUES(content), praise_num=VALUES(praise_num), 
            comments_num=VALUES(comments_num), update_time=VALUES(update_time), crawl_update_time=VALUES(crawl_time)
        '''

        create_time = time.strftime(SQL_DATETIME_FORMAT, time.localtime(self['create_time']))
        update_time = time.strftime(SQL_DATETIME_FORMAT, time.localtime(self['update_time']))
        crawl_time = time.strftime(SQL_DATETIME_FORMAT, time.localtime(self['crawl_time']))

        params = (self['zhihu_id'], self['url'], self['question_id'], self['author_id'], self['content'],
                  self['praise_num'], self['comments_num'], create_time, update_time, crawl_time)

        return insert_sql, params


class LagouJobItemLoader(ItemLoader):
    default_output_processor = TakeFirst()


def remove_splash(value):
    return value.replace('/', '')


def str_strip(value):
    return value.strip()


class LagouJobItem(scrapy.Item):
    url = scrapy.Field()
    url_object_url = scrapy.Field()
    title = scrapy.Field()
    salary = scrapy.Field()
    job_city = scrapy.Field(
        input_processor=MapCompose(remove_splash),
    )
    work_year = scrapy.Field(
        input_processor=MapCompose(remove_splash),
    )
    degree_need = scrapy.Field(
        input_processor=MapCompose(remove_splash),
    )
    job_type = scrapy.Field()
    publish_time = scrapy.Field()
    tags = scrapy.Field(
        output_processor=Join(',')
    )
    job_advantage = scrapy.Field()
    job_desc = scrapy.Field(
        input_processor=MapCompose(remove_tags),
    )
    job_addr = scrapy.Field(
        input_processor=MapCompose(str_strip),
        output_processor=Join('')
    )
    company_url = scrapy.Field()
    company_name = scrapy.Field()
    crawl_time = scrapy.Field()
    crawl_update_time = scrapy.Field()

    def get_insert_sql(self):
        insert_sql = '''
               insert into lagou_job(url, url_object_url, title, salary, job_city, work_year, degree_need, 
               job_type, publish_time, tags, job_advantage, job_desc, job_addr, company_url, company_name, crawl_time) 
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
               on duplicate KEY UPDATE salary=VALUES(salary), job_city=VALUES(job_city), work_year=VALUES(work_year),
               degree_need=VALUES(degree_need), publish_time=VALUES(publish_time), crawl_update_time=VALUES(crawl_time)
           '''

        crawl_time = self['crawl_time'].strftime(SQL_DATETIME_FORMAT)

        params = (self['url'], self['url_object_url'], self['title'], self['salary'], self['job_city'],
                  self['work_year'], self['degree_need'], self['job_type'], self['publish_time'], self['tags'],
                  self['job_advantage'], self['job_desc'], self['job_addr'], self['company_url'], self['company_name'],
                  crawl_time)

        return insert_sql, params
