# -*- coding: utf-8 -*-

import re
import config
import utils
import pdb


from scrapy import Request
from scrapy.spider import Spider
from scrapy.http import FormRequest
from scrapy.http.cookies import CookieJar
from scrapy.selector import Selector
from sqlhelper import SqlHelper
import datetime
import json



class YishouItem(Spider):
    name = 'yishou_item'

    base_url = 'http://api.yishouapp.com/'
    goods_url = base_url + 'goods/get_goods_info'

    header = {
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-Hans-CN;q=1, en-CN;q=0.9, ja-CN;q=0.8, zh-Hant-CN;q=0.7, zh-HK;q=0.6, ja-JP;q=0.5',
        'Host':'api.yishouapp.com',
        'Cookie':'PHPSESSID=fra9s6rjsppv7js33ldj9qbbc1; UM_distinctid=15beb338e6655-0ac2511fb5fdd68-3a156b58-3d10d-15beb338e677c',
        'Content-Type':'application/x-www-form-urlencoded',
        'User-Agent':'YiShou/1.4 (iPhone; iOS 10.3.1; Scale/2.00)',
    }


    def __init__(self, *a , **kw):
        super(YishouItem, self).__init__(*a, **kw)

        self.dir_name = 'log/%s' % self.name
        self.sql = SqlHelper()
        self.init()
        utils.make_dir(self.dir_name)

    def init(self):
        self.create_item_table()


    def start_requests(self):
        now = datetime.datetime.now().strftime('%Y-%m-%d')
        command = "SELECT * FROM {0} z WHERE `create_time` >= \'{1}\'  AND NOT EXISTS ( SELECT 1 FROM {0} WHERE create_time < \'{1}\' AND `goods_no` =  z.`goods_no` ) AND finished = 0".format(config.yishou_activity_detail_table,now)
        data = self.sql.query(command)
        utils.key_print(len(data))
        for i, item in enumerate(data):
            formData = {"goods_id":str(item[2])}
            yield FormRequest(
                url = self.goods_url,
                formdata = formData,
                headers = self.header,
                meta = {
                    'footprint':'1',
                    'goods_id' :item[2],
                    'activity_id':item[1]
                },
                callback = self.parse_item,
                errback = self.error_parse_item,
            )

    def parse_item(self,response):
        if response.status == 200:
            json_success = False
            try:
                data = json.loads(response.body)
                item_data = data['data']
                json_success = True
            except:
                utils.key_print(response.body)
            if json_success:
                item_data = data['data']
                utils.log('parse item:%s' % (item_data['goods_name']))
                #print('%s msg:%s \n' % (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), item_data['goods_name'].encode('utf-8')))
                dt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                msg = (None,response.meta.get('goods_id'),response.meta.get('activity_id'),dt,'yishou',0,json.dumps(item_data))
                command = ("INSERT IGNORE INTO {}"
                        "(id,item_id,activity_id,create_time,channel,status,content)"
                        "VALUES(%s,%s,%s,%s,%s,%s,%s)".format(config.yishou_item_table)
                )
                self.sql.insert_data(command, msg)

                command = "UPDATE {0} SET finished = 1 WHERE goods_id=\'{1}\'".format(config.yishou_activity_detail_table,response.meta.get('goods_id'))
                self.sql.execute(command)
            else:
                formData = {"goods_id":response.meta.get('goods_id')}
                yield FormRequest(
                    url = self.goods_url,
                    formdata = formData,
                    headers = self.header,
                    meta = {
                        'footprint':'1',
                        'goods_id' :response.meta.get('goods_id'),
                        'activity_id':response.meta.get('activity_id')
                    },
                    callback = self.parse_item,
                    errback = self.error_parse_item,
                )
    def error_parse_item(self,response):
        request = faiture.request
        utils.log('error_parse url:%s meta:%s' % (request.url, request.meta))
    def save_page(self, file_name, data):
        with open(file_name, 'w') as f:
            f.write(data)
            f.close()
    def create_item_table(self):
        command = (
            "CREATE TABLE IF NOT EXISTS {} ("
            "`id` INT(8) NOT NULL AUTO_INCREMENT,"
            "`item_id` INT(20) NOT NULL COMMENT '商品ID',"
            "`activity_id` INT(5) NOT NULL COMMENT '专题ID',"
            "`create_time` DATETIME NOT NULL COMMENT `插入时间`,"
            "`channel` CHAR(20) NOT NULL COMMENT `渠道，yishou 或者tiantian`,"
            "`status` INT(2) NOT NULL COMMENT `商品同步状态，0未操作，1操作完成`,"
            "`content` TEXT NOT NULL COMMENT `原始数据`,"
            "PRIMARY KEY(id),"
            "UNIQUE KEY `item_id` (`item_id`)"
            ") ENGINE=InnoDB".format(config.yishou_item_table)
        )
        self.sql.create_table(command)
