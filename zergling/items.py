# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy
import six

class ZerglingItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    datas = scrapy.Field()
    website_name = scrapy.Field()
    column_name = scrapy.Field()
    platform = scrapy.Field()
    url = scrapy.Field()
    crawled_at = scrapy.Field()

    # def __init__(self, collection):
    #     print collection, "||||||||||||||"
    #     if collection:
    #         for i in collection:
    #             name = i["name"]
    #             self.fields[name] = scrapy.Field()
    #             print self.fields, "***************"