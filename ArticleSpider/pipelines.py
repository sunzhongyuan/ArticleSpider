# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
from scrapy.pipelines.images import ImagesPipeline
import codecs   # python2中用这个读写文件可以避免字符编码问题，python3中直接用open打开就行
import json
from scrapy.exporters import JsonItemExporter   # scrapy提供的用于将item导出成Json模式，还支持其他模式
import MySQLdb  # 用于创建数据库链接
import MySQLdb.cursors
from twisted.enterprise import adbapi   # 提供异步容器，这里用于异步操作数据库


class ArticlespiderPipeline(object):
    def process_item(self, item, spider):
        return item


# 导出json文件第一种方法：手动进行json文件的导出
class JsonWithEncodingPipeline(object):
    # 自定义json文件的导出
    def __init__(self):
        # 打开一个json文件
        self.file = codecs.open('article.json', 'w', encoding='utf-8')

    def process_item(self, item, spider):
        # item转换为json模式，ensure_ascii=False如果不写这个的话写入中文的时候会乱码，写了这个字符会以unicode的模式转换为json
        lines = json.dumps(dict(item), ensure_ascii=False)
        # 把生成的json串写入json文件
        self.file.write(lines)
        return item

    # 在这个函数里关闭文件
    def spider_close(self, spider):
        self.file.close()


# 插入数据库第一种方法：同步插入mysql数据库
class MysqlPipeline(object):
    def __init__(self):
        self.conn = MySQLdb.connect('127.0.0.1', 'root', '1218', 'article_spider', charset='utf8', use_unicode=True)
        self.cursor = self.conn.cursor()

    def process_item(self, item, spider):
        insert_sql = '''
            insert into article(title, url, url_object_id, create_date, fav_nums)
            values (%s, %s, %s, %s, %s)
        '''
        # cursor.execute是同步执行
        self.cursor.execute(insert_sql, (item['title'], item['url'], item['url_object_id'], item['create_date'], item['fav_nums']))
        self.conn.commit()


# 导出json文件第二种方法：利用scrapy提供的模块导出json文件
class JsonExporterPipeline(object):
    def __init__(self):
        self.file = open('article_export.json', 'wb')   # 以二进制的方式打开
        self.exporter = JsonItemExporter(self.file, encoding='utf-8', ensure_ascii=False)   # 实例化JsonItemExporter
        self.exporter.start_exporting()     # 第一步start_exporting

    def spider_close(self, spider):
        self.exporter.finish_exporting()    # 第三步finish_exporting
        self.file.close()

    def process_item(self, item, spider):
        self.exporter.export_item(item)     # 第二步export_item
        return item


# 插入数据库第二种方法：利用twisted异步插入数据库
class MysqlTwistedPipeline(object):
    def __init__(self, dbpool):
        self.dbpool = dbpool

    @classmethod    # 类方法，类不用实例化就可以调用的方法
    def from_settings(cls, settings):   # 这个方法sipder会调用，将setting文件传入， 在这里可以获取setting文件内容
        dbparms = dict(
            host=settings['MYSQL_HOST'],    # 这样获取setting文件参数
            db=settings['MYSQL_DBNAME'],
            user=settings['MYSQL_USER'],
            password=settings['MYSQL_PASSWORD'],
            charset='utf8',
            cursorclass=MySQLdb.cursors.DictCursor,
            use_unicode=True
        )   # 这些是连接数据库需要的参数，key值对应MySQLdb.connect的参数名
        dbpool = adbapi.ConnectionPool('MySQLdb', **dbparms)    # 生成连接池，目前只支持关系型数据库

        return cls(dbpool)  # 返回一个当前类的实例

    def process_item(self, item, spider):
        query = self.dbpool.runInteraction(self.do_insert, item)    # 利用twisted异步执行sql语句
        query.addErrback(self.handle_error, item, spider)     # 处理异步执行的异常，传入item是为了查看哪个item出错

    # 这个函数打印sql错误信息，传入item、spider便于查看哪错了
    # 调试时可以在这里打断点，及时发现错误
    def handle_error(self, failure, item, spider):
        print(failure)

    # 这里执行具体的sql语句
    # 为了达到公用的目的，避免每个item都写一个sql，这里将sql语句写在了item的get_insert_sql函数里，
    # 调用get_insert_sql方法得到insert语句，执行这个语句即可
    def do_insert(self, cursor, item):
        insert_sql, params = item.get_insert_sql()
        cursor.execute(insert_sql, params)


# 继承自ImagesPipeline，ImagesPipeline是scrappy提供的下载图片模块，重写这个类的方法可以自定义一些功能
class ArticleImagePipeline(ImagesPipeline):
    def item_completed(self, results, item, info):      # 重写这个方法可以获取图片文件保存到本地的路径
        if 'front_image_url' in item:  # 公共下载模块，如果没有图片要下载，就不执行以下获取图片存储路径的语句，否则会报错
            for ok, value in results:   # results中存储了图片存放的路径，results是一个元祖(True or False, {'path':'full/image.jpg'})
                image_file_path = value['path']
            item["front_image_path"] = image_file_path
        return item

