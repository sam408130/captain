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


class TTActivityDetail(Spider):
    name = 'tt_activity_detail'

    base_url = 'http://api2.nahuo.com/v3/pinhuoitem/getitemsv2'

    header = {
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-Hans-CN;q=1, en-CN;q=0.9, ja-CN;q=0.8, zh-Hant-CN;q=0.7, zh-HK;q=0.6, ja-JP;q=0.5',
        'Host':'api2.nahuo.com',
        'Cookie':'NaHuo.UserLogin=EB434C077BAA01DDF7224295A519B9F8D8306D4C4B43661B36AC03C185A6144697FFA877A98E26946A23782677A23551B7089C2447321818938BE4B54084925B6D1DFE953C0301182026FCC54625A709660821CE5047529E3DFAD9B034CA25855490203A27ACFCFC2B49784D91A89A43BBE0580FBEF946F91F8D456DFDD470BE7B2D5E2DAD7C15B86B8B08CD748991114C35366818BBC90620A19FB7F1084F07C24F155043C301B0160386660FB0C66368877C6D8499B8B631501630A4DA6F6E533A72150E82625FA604992A3DE6EC4B557F08E492F4F7DF31F0C2BA9D48F4AA9265C84BD655A9EA9208111CEBCA35007DE4BE4899B46FE780004070F01D88FBBEB9013B3ED7A5485FB840A64F83AD7DEFD6E3092C91A1CC8C0242077F00AC086C10284967E7157E6F254C5756DDCEC5648751E015F37D4DA79C0F4C525C988EDEAADB4CD632AD8372C84974CE9F021084C1C3DD4D62265D78E1733901E802F9E1BE90192A4042081D39FB10F685649ADCE78B8BC1DA4BB689ED991B33E37D1838BED3FE1311722F8C88036117A4934C8C22ECF66CD8ED645E902F6C3A9DEC3CA596E4C21B908890E888518542F675CBBD10E6EAAC59974213E62945C392F15B00A7646139664450CB4780D4BA15594453FF7A0D8C22FB6E0BD10494DF2E9A25066DCDC1; domain=nahuo.com; expires=Thu, 13-Jul-2017 01:47:23 GMT; path=/; HttpOnly',
        'Content-Type':'application/x-www-form-urlencoded',
        'User-Agent':'QuickSaling/2.3.3 (iPhone; iOS 10.3.2; Scale/2.00)',
    }

    def __init__(self, *a , **kw):
        super(TTActivityDetail, self).__init__(*a, **kw)

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
        command = "SELECT * from {0} WHERE create_time >= \'{1}\' AND finished = 0".format(config.tt_activity_table,now)
        data = self.sql.query(command)
        for i, activity in enumerate(data):
            page = activity[5]
            activity_id = activity[1]
            displayMode = 0
            if page > 1:displayMode = 1
            param = "?displayMode=%s&pageIndex=%s&pageSize=20&qsid=%s" % (displayMode,str(page),activity_id)
            utils.key_print(param)
            yield Request(
                url = self.base_url + param,
                headers = self.header,
                meta = {
                    'pageIndex' : page,
                    'activity_id': activity_id
                },
                callback = self.parse_activity_detail,
                errback = self.error_parse_activity_detail,
            )


    def parse_activity_detail(self,response):

        if response.status == 200:
            json_success = False
            try:
                data = json.loads(response.body)
                items = data['Data']['NewItems']
                json_success = True
            except:
                utils.key_print(response.body)
            if json_success:
                items = data['Data']['NewItems']
                activity_id = response.meta.get('activity_id')
                if len(items) > 0:
                    for item in items:
                        utils.log('parse activity:%s , page: %s ,parse item:%s' % (activity_id,response.meta.get('pageIndex'),item['Title']))
                        dt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        msg = (None ,activity_id, item['ID'],item['Title'],item['Cover'].replace('upyun:nahuo-img-server://','https://nahuo-img-server.b0.upaiyun.com/').replace('upyun:item-img:/','http://item-img.b0.upaiyun.com/'),item['Price'],item['DealCount'],dt,0)
                        command = ("INSERT IGNORE INTO {} "
                                "(id,activity_id,goods_id,goods_name,goods_img,price,deal_count,create_time,finished)"
                                "VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)".format(config.tt_activity_detail_table)
                        )
                        self.sql.insert_data(command, msg)

                    command = "UPDATE {0} SET page = \'{1}\' WHERE activity_id=\'{2}\'".format(config.tt_activity_table,str(response.meta.get('pageIndex')+1) ,response.meta.get('activity_id'))
                    self.sql.execute(command)

                    if len(items) < 20:
                        command = "UPDATE {0} SET finished = 1 WHERE activity_id=\'{1}\'".format(config.tt_activity_table,response.meta.get('activity_id'))
                        self.sql.execute(command)

                    page = response.meta.get('pageIndex') + 1
                    if page > 1:displayMode = 1
                    param = "?displayMode=%s&pageIndex=%s&pageSize=20&qsid=%s" % (displayMode,str(page),activity_id)
                    utils.key_print(param)
                    yield Request(
                        url = self.base_url + param,
                        headers = self.header,
                        meta = {
                            'pageIndex' : page,
                            'activity_id': activity_id
                        },
                        callback = self.parse_activity_detail,
                        errback = self.error_parse_activity_detail,
                    )
                if len(items) == 0:
                    command = "UPDATE {0} SET finished = 1 WHERE activity_id=\'{1}\'".format(config.tt_activity_table,response.meta.get('activity_id'))
                    self.sql.execute(command)
            else:
                page = response.meta.get('pageIndex')
                activity_id = response.meta.get('activity_id')
                if page > 1:displayMode = 1
                param = "?displayMode=%s&pageIndex=%s&pageSize=20&qsid=%s" % (displayMode,str(page),activity_id)
                utils.key_print(param)
                yield Request(
                    url = self.base_url + param,
                    headers = self.header,
                    meta = {
                        'pageIndex' : page,
                        'activity_id': activity_id
                    },
                    callback = self.parse_activity_detail,
                    errback = self.error_parse_activity_detail,
                )
        else:
            page = response.meta.get('pageIndex')
            activity_id = response.meta.get('activity_id')
            if page > 1:displayMode = 1
            param = "?displayMode=%s&pageIndex=%s&pageSize=20&qsid=%s" % (displayMode,str(page),activity_id)
            utils.key_print(param)
            yield Request(
                url = self.base_url + param,
                headers = self.header,
                meta = {
                    'pageIndex' : page,
                    'activity_id': activity_id
                },
                callback = self.parse_activity_detail,
                errback = self.error_parse_activity_detail,
            )

    def error_parse_activity_detail(self, failure):
        request = failure.request
        utils.log('error_parse url:%s meta:%s' % (request.url, request.meta))

        page = response.meta.get('pageIndex')
        activity_id = response.meta.get('activity_id')
        if page > 1:displayMode = 1
        param = "?displayMode=%s&pageIndex=%s&pageSize=20&qsid=%s" % (displayMode,str(page),activity_id)
        utils.key_print(param)
        yield Request(
            url = self.base_url + param,
            headers = self.header,
            meta = {
                'pageIndex' : page,
                'activity_id': activity_id
            },
            callback = self.parse_activity_detail,
            errback = self.error_parse_activity_detail,
        )

    def create_activity_detail_table(self):
        command = (
            "CREATE TABLE IF NOT EXISTS {} ("
            "`id` INT(8) NOT NULL AUTO_INCREMENT,"
            "`activity_id` INT(8) NOT NULL,"
            "`goods_id` INT(8) NOT NULL,"
            "`goods_name` TEXT NOT NULL,"
            "`goods_img` TEXT NOT NULL,"
            "`price` CHAR(10) NOT NULL,"
            "`deal_count` INT(5) NOT NULL,"
            "`create_time` DATETIME NOT NULL,"
            "`finished` INT(2) NOT NULL,"
            "PRIMARY KEY(id),"
            "UNIQUE KEY `goods_id` (`goods_id`)"
            ") ENGINE=InnoDB".format(config.tt_activity_detail_table)
        )
        self.sql.create_table(command)
