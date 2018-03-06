# -*- coding: utf-8 -*-
import os
import sys

# Scrapy settings for ArticleSpider project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#     http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html
#     http://scrapy.readthedocs.org/en/latest/topics/spider-middleware.html

BOT_NAME = 'ArticleSpider'

SPIDER_MODULES = ['ArticleSpider.spiders']
NEWSPIDER_MODULE = 'ArticleSpider.spiders'


# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'ArticleSpider (+http://www.yourdomain.com)'

# Obey robots.txt rules
ROBOTSTXT_OBEY = False  # 爬取时是否过滤指定URL

# Configure maximum concurrent requests performed by Scrapy (default: 16)
#CONCURRENT_REQUESTS = 32

# Configure a delay for requests for the same website (default: 0)
# See http://scrapy.readthedocs.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
#DOWNLOAD_DELAY = 3
# The download delay setting will honor only one of:
#CONCURRENT_REQUESTS_PER_DOMAIN = 16
#CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
#COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
# DEFAULT_REQUEST_HEADERS = {
#   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#   'Accept-Language': 'en',
# }
# DEFAULT_REQUEST_HEADERS = {
#   'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36'
# }

# Enable or disable spider middlewares
# See http://scrapy.readthedocs.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    'ArticleSpider.middlewares.ArticlespiderSpiderMiddleware': 543,
#}

# Enable or disable downloader middlewares
# See http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
   'ArticleSpider.middlewares.MyCustomDownloaderMiddleware': 543,
}

# Enable or disable extensions
# See http://scrapy.readthedocs.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    'scrapy.extensions.telnet.TelnetConsole': None,
#}

# Configure item pipelines
# See http://scrapy.readthedocs.org/en/latest/topics/item-pipeline.html
# 抓取页面数据存放到item，然后会到setting文件找到这个ITEM_PIPELINES，根据后面到数字依次调用
ITEM_PIPELINES = {
    # 'ArticleSpider.pipelines.JsonExporterPipeline': 2,
    # 'scrapy.pipelines.images.ImagesPipeline': 1,    # 下载图片模块，scrapy自带，1代表执行顺序，数字越小🈷️越先执行
    # 'ArticleSpider.pipelines.ArticleImagePipeline': 1,  # 重写下载图片模块方法，保存图片本地存储路径
    # 'ArticleSpider.pipelines.MysqlPipeline': 1,  # 同步存入数据库，连接mysql，并保存数据到mysql数据库
    'ArticleSpider.pipelines.MysqlTwistedPipeline': 1,  # 异步存入数据库，连接mysql，并保存数据到mysql数据库
}
IMAGES_URLS_FIELD = 'front_image_url'   # 要下载的图片的URL地址字段，这字段需要赋值成数组
project_dir = os.path.abspath(os.path.dirname(__file__))    # 获取当前文件的目录
IMAGES_STORE = os.path.join(project_dir, 'images')  # 下载的图片存放到本地的地址
# 想要下载图片还要安装一个pillow模块，pip install pillow

# 设置pythonpath
# 相当于将/Users/zyzy/PyCharmProject/ArticleSpider/ArticleSpider设置为sources root
# import时可以直接import utils；而不需要import ArticleSpider.utils
print(project_dir)
sys.path.insert(0, project_dir)

# Enable and configure the AutoThrottle extension (disabled by default)
# See http://doc.scrapy.org/en/latest/topics/autothrottle.html
#AUTOTHROTTLE_ENABLED = True
# The initial download delay
#AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = 'httpcache'
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'

MYSQL_HOST = '127.0.0.1'
MYSQL_DBNAME = 'article_spider'
MYSQL_USER = 'root'
MYSQL_PASSWORD = '1218'

SQL_DATETIME_FORMAT = '%Y-%m-%d %H-%M-%S'
SQL_DATE_FORMAT = '%Y-%m-%d'

CRAWLSPIDER_FOLLOW_LINKS = True
