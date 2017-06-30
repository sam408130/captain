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



class TTActivity(Spider):
    name = 'tt_activity'

    base_url = 'http://api2.nahuo.com/v3/pinhuoitem/GetAllActivitys'

    header = {
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-Hans-CN;q=1, en-CN;q=0.9, ja-CN;q=0.8, zh-Hant-CN;q=0.7, zh-HK;q=0.6, ja-JP;q=0.5',
        'Host':'api2.nahuo.com',
        'Cookie':'NaHuo.UserLogin=EB434C077BAA01DDF7224295A519B9F8D8306D4C4B43661B36AC03C185A6144697FFA877A98E26946A23782677A23551B7089C2447321818938BE4B54084925B6D1DFE953C0301182026FCC54625A709660821CE5047529E3DFAD9B034CA25855490203A27ACFCFC2B49784D91A89A43BBE0580FBEF946F91F8D456DFDD470BE7B2D5E2DAD7C15B86B8B08CD748991114C35366818BBC90620A19FB7F1084F07C24F155043C301B0160386660FB0C66368877C6D8499B8B631501630A4DA6F6E533A72150E82625FA604992A3DE6EC4B557F08E492F4F7DF31F0C2BA9D48F4AA9265C84BD655A9EA9208111CEBCA35007DE4BE4899B46FE780004070F01D88FBBEB9013B3ED7A5485FB840A64F83AD7DEFD6E3092C91A1CC8C0242077F00AC086C10284967E7157E6F254C5756DDCEC5648751E015F37D4DA79C0F4C525C988EDEAADB4CD632AD8372C84974CE9F021084C1C3DD4D62265D78E1733901E802F9E1BE90192A4042081D39FB10F685649ADCE78B8BC1DA4BB689ED991B33E37D1838BED3FE1311722F8C88036117A4934C8C22ECF66CD8ED645E902F6C3A9DEC3CA596E4C21B908890E888518542F675CBBD10E6EAAC59974213E62945C392F15B00A7646139664450CB4780D4BA15594453FF7A0D8C22FB6E0BD10494DF2E9A25066DCDC1; domain=nahuo.com; expires=Thu, 13-Jul-2017 01:47:23 GMT; path=/; HttpOnly',
        'Content-Type':'application/x-www-form-urlencoded',
        'User-Agent':'QuickSaling/2.3.3 (iPhone; iOS 10.3.2; Scale/2.00)',
    }

    def __init__(self, *a , **kw):
        super(TTActivity, self).__init__(*a, **kw)

        self.dir_name = 'log/%s' % self.name
        self.sql = SqlHelper()
        self.init()
        utils.make_dir(self.dir_name)


    def init(self):
        self.create_activity_table()

    def start_requests(self):
        return self.start_requests_activity()


    def start_requests_activity(self):
        pageindex = 1
        param = "?pagesize=20&pageIndex=%s" % (str(pageindex))
        yield Request(
            url = self.base_url + param,
            headers = self.header,
            meta = {
                'pageIndex' : pageindex
            },
            callback = self.parse_activity,
        )

    def parse_activity(self,response):
        if response.status == 200:
            data = json.loads(response.body)
            activities = data["Data"]["ActivityList"]
            now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if len(activities) > 0:
                for activity in activities:
                    if activity['Times'] > 0:
                        msg = (None,activity['QsID'],activity['Name'],activity['Description'],json.dumps(response.body),now,1,0)
                        command = ("INSERT IGNORE INTO {} "
                                "(id,activity_id,activity_name,activity_desc,content,create_time,page,finished)"
                                "VALUES(%s,%s,%s,%s,%s,%s,%s,%s)".format(config.tt_activity_table)
                        )
                        self.sql.insert_data(command, msg)
                        utils.log(activity['Name'])
                pageindex = response.meta.get("pageIndex")+1
                param = "?pagesize=20&pageIndex=%s" % (str(pageindex))
                yield Request(
                    url = self.base_url + param,
                    headers = self.header,
                    meta = {
                        'pageIndex' : pageindex
                    },
                    callback = self.parse_activity,
                )
            else:
                pageindex = response.meta.get("pageIndex")
                param = "?pagesize=20&pageIndex=%s" % (str(pageindex))
                yield Request(
                    url = self.base_url + param,
                    headers = self.header,
                    meta = {
                        'pageIndex' : pageindex
                    },
                    callback = self.parse_activity,
                )



    def create_activity_table(self):
        command = (
            "CREATE TABLE IF NOT EXISTS {} ("
            "`id` INT(8) NOT NULL AUTO_INCREMENT,"
            "`activity_id` INT(8) NOT NULL COMMENT '专题ID',"
            "`activity_name` TEXT NOT NULL,"
            "`activity_desc` TEXT NOT NULL,"
            "`create_time` DATETIME NOT NULL,"
            "`page` INT(5) NOT NULL,"
            "`finished` INT(2) NOT NULl,"
            "`content` TEXT NOT NULL,"
            "PRIMARY KEY(id),"
            "UNIQUE KEY `activity_id` (`activity_id`)"
            ") ENGINE=InnoDB".format(config.tt_activity_table)
        )
        self.sql.create_table(command)

    def save_page(self, file_name, data):
        with open(file_name, 'w') as f:
            f.write(data)
            f.close()
