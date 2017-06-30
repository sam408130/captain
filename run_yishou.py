#-*- coding: utf-8 -*-

import logging
import os
import sys
import utils

from scrapy import cmdline
from scrapy.crawler import CrawlerProcess
from captain.spiders.yishou import Yishou
from captain.spiders.yishou_activity import YishouActivity
from captain.spiders.yishou_item import YishouItem

if __name__ == '__main__':
    utils.log('*******************run spider start...*******************')
    process = CrawlerProcess()
    process.crawl(Yishou)
    process.crawl(YishouActivity)
    process.crawl(YishouItem)
    process.start()
