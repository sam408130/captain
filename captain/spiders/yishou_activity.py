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


class YishouActivity(Spider):
    name = 'yishou_activity'

    base_url = 'http://api.yishouapp.com/'
    homepage_url = base_url + 'Special/get_homepage_data'
    activity_url = base_url + 'goods/get_goods'
    goods_url = base_url + 'goods/get_goods_info'
    login_url = base_url + 'users/login'
    test_url = 'http://m.shangxinpifa.com/api/item/detail/90281'


    header = {
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-Hans-CN;q=1, en-CN;q=0.9, ja-CN;q=0.8, zh-Hant-CN;q=0.7, zh-HK;q=0.6, ja-JP;q=0.5',
        'Host':'api.yishouapp.com',
        'Cookie':'PHPSESSID=fra9s6rjsppv7js33ldj9qbbc1; UM_distinctid=15beb338e6655-0ac2511fb5fdd68-3a156b58-3d10d-15beb338e677c',
        'Content-Type':'application/x-www-form-urlencoded',
        'User-Agent':'YiShou/1.4 (iPhone; iOS 10.3.1; Scale/2.00)',
    }

    def __init__(self, *a , **kw):
        super(YishouActivity, self).__init__(*a, **kw)

        self.dir_name = 'log/%s' % self.name
        self.sql = SqlHelper()
        self.init()
        utils.make_dir(self.dir_name)

    def init(self):

        self.create_activity_detail_table()


    def start_requests(self):

        return self.start_requests_activity_detail()


    def start_requests_activity_detail(self):
        now = datetime.datetime.now().strftime('%Y-%m-%d')
        command = "SELECT * from {0} WHERE special_start_time > \'{1}\' AND finished = 0".format(config.yishou_activity_table,now)
        data = self.sql.query(command)

        for i, activity in enumerate(data):
            page = activity[20]
            special_id = str(activity[1])
            formData = {"pageindex":str(page),"special_id":special_id}
            utils.key_print(formData)

            yield FormRequest(
                url = self.activity_url,
                formdata = formData,
                headers = self.header,
                meta = {
                    'pageindex' : page,
                    'special_id': special_id
                },
                callback = self.parse_activity_detail,
                errback = self.error_parse_activity_detail,
            )
            #break


    def parse_activity_detail(self,response):

        #pdb.set_trace()
        if response.status == 200:
            json_success = False
            try:
                data = json.loads(response.body)
                items = data['data']['goods']
                json_success = True
            except:
                utils.key_print(response.body)
            if json_success:
                items = data['data']['goods']
                special_id = response.meta.get('special_id')
                if len(items) > 0:
                    for item in items:
                        utils.log('parse activity:%s , page: %s ,parse item:%s' % (special_id,response.meta.get('pageindex'),item['goods_name']))
                        dt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        msg = (None, special_id,item['goods_id'],item['cat_id'],item['brand_tag'],item['goods_name'],item['goods_middle'],item['sales'],item['enough_number'],item['shop_price'],item['brand_id'],item['goods_no'],item['sales_of_7'],item['goods_img'],dt,0)
                        command = ("INSERT IGNORE INTO {} "
                                "(id, special_id, goods_id, cat_id, brand_tag, goods_name, goods_middle, sales, enough_number, shop_price, brand_id, goods_no, sales_of_7, goods_img,create_time,finished)"
                                "VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s)".format(config.yishou_activity_detail_table)
                        )
                        self.sql.insert_data(command, msg)


                    #update activity page

                    command = "UPDATE {0} SET page = \'{1}\' WHERE special_id=\'{2}\'".format(config.yishou_activity_table,str(response.meta.get('pageindex')+1) ,response.meta.get('special_id'))
                    self.sql.execute(command)

                    if len(items) < 20:
                        command = "UPDATE {0} SET finished = 1 WHERE special_id=\'{1}\'".format(config.yishou_activity_table,response.meta.get('special_id'))
                        self.sql.execute(command)


                    page = response.meta.get('pageindex') + 1
                    formData = {"pageindex":str(page),"special_id":special_id}
                    utils.key_print(formData)
                    yield FormRequest(
                        url = self.activity_url,
                        formdata = formData,
                        headers = self.header,
                        meta = {
                            'pageindex' : page,
                            'special_id': special_id
                        },
                        callback = self.parse_activity_detail,
                        errback = self.error_parse_activity_detail,
                    )
                if len(items) == 0:
                    command = "UPDATE {0} SET finished = 1 WHERE special_id=\'{1}\'".format(config.yishou_activity_table,response.meta.get('special_id'))
                    self.sql.execute(command)

            else:
                page = response.meta.get('pageindex')
                special_id = response.meta.get('special_id')
                formData = {"pageindex":str(page),"special_id":special_id}
                print 'auth failed'
                utils.key_print(formData)
                yield FormRequest(
                    url = self.activity_url,
                    formdata = formData,
                    headers = self.header,
                    meta = {
                        'pageindex' : page,
                        'special_id': special_id
                    },
                    callback = self.parse_activity_detail,
                    errback = self.error_parse_activity_detail,
                )


        else:
            page = response.meta.get('pageindex')
            special_id = response.meta.get('special_id')
            formData = {"pageindex":str(page),"special_id":special_id}
            utils.key_print(formData)
            yield FormRequest(
                url = self.activity_url,
                formdata = formData,
                headers = self.header,
                meta = {
                    'pageindex' : page,
                    'special_id': special_id
                },
                callback = self.parse_activity_detail,
                errback = self.error_parse_activity_detail,
            )


    def create_activity_detail_table(self):
        command = (
            "CREATE TABLE IF NOT EXISTS {} ("
            "`id` INT(8) NOT NULL AUTO_INCREMENT,"
            "`special_id` INT(8) NOT NULL,"
            "`goods_id` INT(8) NOT NULL COMMENT '商品ID',"
            "`cat_id` INT(8) NOT NULL,"
            "`brand_tag` CHAR(20) NOT NULL,"
            "`goods_name` TEXT NOT NULL,"
            "`goods_middle` TEXT NOT NULL,"
            "`sales` INT(10) NOT NULL,"
            "`enough_number` INT(8) NOT NULL,"
            "`shop_price` CHAR(10) NOT NULL,"
            "`brand_id` INT(8) NOT NULL,"
            "`goods_no` INT(10) NOT NULL,"
            "`sales_of_7` INT(10) NOT NULL,"
            "`goods_img` TEXT NOT NULL,"
            "`create_time` DATETIME NOT NULL,"
            "`finished` INT(2) NOT NULL,"
            "PRIMARY KEY(id),"
            "UNIQUE KEY `goods_id` (`goods_id`)"
            ") ENGINE=InnoDB".format(config.yishou_activity_detail_table)
        )
        self.sql.create_table(command)


    def error_parse_activity_detail(self, failure):
        request = failure.request
        utils.log('error_parse url:%s meta:%s' % (request.url, request.meta))

        page = request.meta.get('pageindex')
        special_id = request.meta.get('special_id')
        formData = {"pageindex":str(page),"special_id":special_id}
        yield FormRequest(
            url = self.activity_url,
            formdata = formData,
            headers = self.header,
            meta = {
                'pageindex' : page,
                'special_id': special_id,
                'error_request' :'yes'
            },
            callback = self.parse_activity_detail,
            errback = self.error_parse_activity_detail,
        )

    def save_page(self, file_name, data):
        with open(file_name, 'w') as f:
            f.write(data)
            f.close()
