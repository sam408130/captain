# -*- coding: utf-8 -*-

import re
import config
import utils


from scrapy.spider import Spider
from scrapy import Request
from scrapy.selector import Selector
from sqlhelper import SqlHelper
import datetime


class Proxy(Spider):
    name = "scrapy_proxy"

    base_url = "http://www.xicidaili.com/nn"

    def __init__(self, *a , **kw):
        super(Proxy, self).__init__(*a, **kw)

    def start_requests(self):
        yield Request(
            url = self.base_url,
            headers = {
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, sdch',
                    'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6',
                    'Connection': 'keep-alive',
                    'Host': 'www.xicidaili.com',
                    'Upgrade-Insecure-Requests': '1',
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.11; rv:51.0) Gecko/20100101 Firefox/51.0',
            },
            callback = self.parse_all,
            errback = self.error_parse
        )

    def parse_all(self,response):
        proxys = response.xpath("//table[@id='ip_list']/tr").extract()
        mat = []
        for proxy in proxys:
            sel = Selector(text = proxy)
            ip = sel.xpath("//td[2]/text()").extract_first()
            port = sel.xpath("//td[3]/text()").extract_first()
            utils.log("grab ip :%s:%s" % (ip,port))
            if ip:
                mat.append(str(ip) + ':'+str(port))
        self.save_page('proxys.txt','\n'.join(mat))

    def error_parse(self, faiture):
        request = faiture.request
        utils.log('error_parse url:%s meta:%s' % (request.url, request.meta))

    def save_page(self, file_name, data):
        with open(file_name, 'w') as f:
            f.write(data)
            f.close()
