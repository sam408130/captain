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


class TTItem(Spider):

    name = 'tt_item'
    base_url = 'http://api2.nahuo.com/v3/pinhuoitem/detail2'

    header = {
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-Hans-CN;q=1, en-CN;q=0.9, ja-CN;q=0.8, zh-Hant-CN;q=0.7, zh-HK;q=0.6, ja-JP;q=0.5',
        'Host':'api2.nahuo.com',
        'Cookie':'NaHuo.UserLogin=DF1C641E789D8A3121F0FFBCAD9DF372833B70F5A1EE7CA43AF08E4B84CE740C4F1FED8FE0B445C7DE583B3267E9026B69E3BBCBDC2C8138F32A6154868EC3807AEB9A06E537882C16E2A2EFA7AF2E1BEAC9030A25C01393287D197A25E1F9EDD9AE28A83F46EDB43E8D2263CAE4B21D8107482B1BD8D606960CDB286714CD36E29B75633DBC2015D0E3840EC908F9180CC3518B7E29D56519E01A7EBBE8A60CCDB03009A224E66F4AFE084D22A17039811D74ECE9EB9E7E8170E34168BCE7B7D037ECDE0F4270374CC1887D5DCD0261D3F267C0DC7D76B6CA6884466205EA969755C6EBB18B93229EE9CB93496109468CA04274D711F9A2114198388BC6A3B2EB9B5DB2E6BD63AF584CE4A71DD69139F2F75C8AC4A7DB24E1AE97F9EAE68ED5D136D042514ED6E17D90111C220A7EBA20FB854CEB4DFE5568598C8EC51102D41573ECE7B3DDFCA4EB83B6AB86437FA282B9DFB003A11C369D5D7D68056AD8E2493BB07D9B407D98BC70EF65A166408B0843DE1667432275E20AE8B760E730B66EC9E1E770DAD74AC4816C1233E6E9BBDF6B51D90B74681946D9FF6D3BE9FA05F8DAC9873ABA70529B2FBB05F8F28138E68E9D176054E489BCC593DFACD660C07C78294187BA5D1FB4D42919808AC14DCD7EA509201D14EB549B4B8C3801AAACBC5F362D; domain=nahuo.com; expires=Thu, 13-Jul-2017 06:43:01 GMT; path=/; HttpOnly',
        'Content-Type':'application/x-www-form-urlencoded',
        'User-Agent':'QuickSaling/2.3.3 (iPhone; iOS 10.3.2; Scale/2.00)',
    }

    def __init__(self, *a , **kw):
        super(TTItem, self).__init__(*a, **kw)

        self.dir_name = 'log/%s' % self.name
        self.sql = SqlHelper()
        self.init()
        utils.make_dir(self.dir_name)

    def init(self):
        self.create_item_table()

    def start_requests(self):
        now = datetime.datetime.now().strftime('%Y-%m-%d')
        command = "SELECT * FROM {0} z WHERE `create_time` >= \'{1}\'  AND NOT EXISTS ( SELECT 1 FROM {0} WHERE create_time < \'{1}\' AND `goods_img` =  z.`goods_img` ) AND finished = 0".format(config.tt_activity_detail_table,now)
        data = self.sql.query(command)
        utils.key_print(len(data))
        for i, item in enumerate(data):
            param = '?id=%s&qsid=%s' % (item[2],item[1])
            yield Request(
                url = self.base_url + param,
                headers = self.header,
                meta = {
                    'activity_id':item[1],
                    'goods_id':item[2]
                },
                callback = self.parse_item,
                errback = self.error_parse_item,
            )

    def parse_item(self,response):
        if response.status == 200:
            json_success = False
            try:
                data = json.loads(response.body)
                item_data = data['Data']
                json_success = True
            except:
                utils.key_print(response.body)
            if json_success:
                item_data = data['Data']
                utils.log('parse item:%s' % (item_data['Name']))
                dt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                msg = (None,response.meta.get('goods_id'),dt,'tiantian',0,json.dumps(item_data))
                command = ("INSERT IGNORE INTO {}"
                        "(id,item_id,create_time,channel,status,content)"
                        "VALUES(%s,%s,%s,%s,%s,%s)".format(config.tt_item_table)
                )
                self.sql.insert_data(command, msg)

                command = "UPDATE {0} SET finished = 1 WHERE goods_id=\'{1}\'".format(config.tt_activity_detail_table,response.meta.get('goods_id'))
                self.sql.execute(command)
            else:
                param = '?id=%s&qsid=%s' % (response.meta.get('goods_id'),response.meta.get('activity_id'))
                yield Request(
                    url = self.base_url+param,
                    headers = self.header,
                    meta = {
                        'activity_id':item[1],
                        'goods_id':item[2]
                    },
                    callback = self.parse_item,
                    errback = self.error_parse_item,

                )

    def error_parse_item(self,response):
        request = faiture.request
        utils.log('error_parse url:%s meta:%s' % (request.url, request.meta))


    def create_item_table(self):
        command = (
            "CREATE TABLE IF NOT EXISTS {} ("
            "`id` INT(8) NOT NULL AUTO_INCREMENT,"
            "`item_id` INT(20) NOT NULL,"
            "`create_time` DATETIME NOT NULL,"
            "`channel` CHAR(20) NOT NULL,"
            "`status` INT(2) NOT NULL,"
            "`content` TEXT NOT NULL,"
            "PRIMARY KEY(id),"
            "UNIQUE KEY `item_id` (`item_id`)"
            ") ENGINE=InnoDB".format(config.tt_item_table)
        )
        self.sql.create_table(command)
