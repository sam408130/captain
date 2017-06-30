#-*- coding: utf-8 -*-

import logging
import os
import sys
import utils

from scrapy import cmdline
from scrapy.crawler import CrawlerProcess
from captain.spiders.proxy import Proxy
from captain.spiders.yishou import Yishou
from captain.spiders.yishou_activity import YishouActivity

if __name__ == '__main__':

    # process = CrawlerProcess()
    # process.crawl(Proxy)
    # process.crawl(Yishou)
    # process.crawl(YishouActivity)
    # process.start()

    reload(sys)
    sys.setdefaultencoding('utf-8')

    if not os.path.exists('log'):
        os.makedirs('log')

    logging.basicConfig(
        filename = 'log/item.log',
        format = '%(levelname)s %(asctime)s: %(message)s',
        level = logging.DEBUG
    )


    utils.log('*******************run spider start...*******************')


    #cmdline.execute('scrapy crawl scrapy_proxy'.split())


    #cmdline.execute('scrapy crawl yishou'.split())
    #cmdline.execute('scrapy crawl yishou_activity'.split())
    #cmdline.execute('scrapy crawl yishou_item'.split())
    #cmdline.execute('scrapy crawl tt_activity'.split())
    #cmdline.execute('scrapy crawl tt_activity_detail'.split())
    #cmdline.execute('scrapy crawl tt_item'.split())
    utils.upload_data()
    #utils.fix_item()
