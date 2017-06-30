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


class Yishou(Spider):
    name = 'yishou'

    base_url = 'http://api.yishouapp.com/'
    homepage_url = base_url + 'Special/get_homepage_data'
    activity_url = base_url + 'goods/get_goods'
    goods_url = base_url + 'goods/get_goods_info'
    login_url = base_url + 'users/login'
    test_url = 'http://m.shangxinpifa.com/api/item/detail/90281'

    filter_url = base_url + 'goods/get_goods_filter'

    header = {
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-Hans-CN;q=1, en-CN;q=0.9, ja-CN;q=0.8, zh-Hant-CN;q=0.7, zh-HK;q=0.6, ja-JP;q=0.5',
        'Host':'api.yishouapp.com',
        'Cookie':'PHPSESSID=fra9s6rjsppv7js33ldj9qbbc1; UM_distinctid=15beb338e6655-0ac2511fb5fdd68-3a156b58-3d10d-15beb338e677c',
        'Content-Type':'application/x-www-form-urlencoded',
        'User-Agent':'YiShou/1.4 (iPhone; iOS 10.3.1; Scale/2.00)',
    }

    def __init__(self, *a , **kw):
        super(Yishou, self).__init__(*a, **kw)

        self.dir_name = 'log/%s' % self.name
        self.sql = SqlHelper()
        self.init()
        utils.make_dir(self.dir_name)

    def init(self):
        self.create_activity_table()

    def start_requests(self):
        return self.start_requests_activity()
        #return self.start_requests_filter()




    def start_requests_filter(self):
        params = 'abcdefghijklmnopqrstuvwxyz0123456789'
        for c in params:
            utils.key_print(c)
            formData = {"keyword":c}
            yield FormRequest(
                url = self.filter_url,
                formdata = formData,
                headers = self.header,
                callback = self.parse_filter
            )

    def parse_filter(self,response):
        if response.status == 200:
            data = json.loads(response.body)
            cats = data['data']['cat']
            brands = data['data']['brand']
            for cat in cats:
                msg = (None, cat['cat_id'],cat['cat_name'])
                command = ("INSERT IGNORE INTO categories"
                    "(id,cat_id,name)"
                    "VALUES(%s,%s,%s)"
                )
                self.sql.insert_data(command,msg)


    def start_requests_activity(self):
        pageindex = 1
        formData = {"module_type":"1","pageindex":str(pageindex)}
        yield FormRequest(
            url = self.homepage_url,
            formdata = formData,
            headers = self.header,
            meta = {
                'pageindex' : pageindex
            },
            callback = self.parse_activity,
        )

    def parse_activity(self,response):
        if response.status == 200:
            data = json.loads(response.body)
            activities = data["data"]

            if len(activities) > 0:
                for activity in activities:
                    msg = (None, activity['special_id'], activity['special_name'],activity['special_thumb'], datetime.datetime.fromtimestamp(float(activity['special_start_time'])),datetime.datetime.fromtimestamp(float(activity['special_end_time'])),activity['special_add_admin'],
                            datetime.datetime.fromtimestamp(float(activity['special_add_time'])),activity['special_status'],activity['special_description'],activity['special_desc'],activity['special_sort'],activity['special_show'],
                            activity['special_period'],activity['special_extra_name'],activity['special_hits'],activity['special_type'],activity['special_style_type'],activity['picker_group'],activity['spacial_title']
                    )
                    command = ("INSERT IGNORE INTO {} "
                                "(id, special_id, special_name, special_thumb, special_start_time, special_end_time, special_add_admin, special_add_time, special_status, special_description, special_desc, special_sort, special_show,special_period,special_extra_name,special_hits,special_type,special_style_type,picker_group,special_title)"
                                "VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)".format(config.yishou_activity_table)
                    )
                    self.sql.insert_data(command, msg)
                    utils.log(activity['special_name'])
                pageindex = response.meta.get("pageindex")+1
                formData = {"module_type":"1","pageindex":str(pageindex)}
                yield FormRequest(
                    url = self.homepage_url,
                    formdata = formData,
                    headers = self.header,
                    meta = {
                        'pageindex' : pageindex
                    },
                    callback = self.parse_activity,
                )
        else:
            pageindex = response.meta.get("pageindex")
            formData = {"module_type":"1","pageindex":str(pageindex)}
            yield FormRequest(
                url = self.homepage_url,
                formdata = formData,
                headers = self.header,
                meta = {
                    'pageindex' : pageindex
                },
                callback = self.parse_activity,
            )

    def create_activity_table(self):
        command = (
            "CREATE TABLE IF NOT EXISTS {} ("
            "`id` INT(8) NOT NULL AUTO_INCREMENT,"
            "`special_id` INT(8) NOT NULL COMMENT '专题ID',"
            "`special_name` TEXT NOT NULL,"
            "`special_thumb` TEXT NOT NULL,"
            "`special_start_time` DATETIME NOT NULL,"
            "`special_end_time` DATETIME NOT NULL,"
            "`special_add_admin` INT(10) NOT NULL,"
            "`special_add_time` DATETIME NOT NULL,"
            "`special_status` INT(8) NOT NULL,"
            "`special_description` TEXT NOT NULL,"
            "`special_desc` TEXT NOT NULL,"
            "`special_sort` INT(8) NOT NULL,"
            "`special_show` INT(8) NOT NULL,"
            "`special_period` INT(10) NOT NULL,"
            "`special_extra_name` TEXT NOT NULL,"
            "`special_hits` INT(10) NOT NULL,"
            "`special_type` INT(8) NOT NULL,"
            "`special_style_type` INT(8) NOT NULL,"
            "`picker_group` INT(8) NOT NULL,"
            "`special_title` TEXT NOT NULL,"
            "PRIMARY KEY(id),"
            "UNIQUE KEY `special_id` (`special_id`)"
            ") ENGINE=InnoDB".format(config.yishou_activity_table)
        )
        self.sql.create_table(command)



    def save_page(self, file_name, data):
        with open(file_name, 'w') as f:
            f.write(data)
            f.close()
