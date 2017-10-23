# -*- coding: utf-8 -*-

import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import Rule
from scrapy_redis.spiders import RedisCrawlSpider
from scrapy_redis.utils import bytes_to_str
from urlparse import urlparse
from goose import Goose
from goose.text import StopWordsChinese
from ..items import ZerglingItem
from lxml import etree
import json

class JetyunSpider(RedisCrawlSpider):
    name = 'jetyun'

    rules = (
    )

    def make_request_from_data(self, data):
        self.config_json = json.loads(bytes_to_str(data, self.redis_encoding));
        url = self.config_json["start_url"]
        extract_links = self.config_json["extracts"]
        follow_links = self.config_json["follows"]
        if extract_links:
            if follow_links:
                self.rules +=(
                    Rule(LinkExtractor(allow=( follow_links ))),
                )
            self.rules += (
                Rule(LinkExtractor(allow=( extract_links )), callback='parse_item'),
            )
            self._compile_rules()
        return self.make_requests_from_url(url)

    def parse_item(self, response):
        g = Goose({'stopwords_class': StopWordsChinese})
        article = g.extract(raw_html=response.body)
        item = ZerglingItem()
        infos = article.infos
        item["website_name"] = self.config_json["website_name"]
        if self.config_json["column_name"]:
            item["column_name"] = self.config_json["column_name"]
        collections = self.config_json["collections"]
        for c in collections:
            name = str(c["name"])
            value = None
            if c.has_key("xpath") and c["xpath"]:
                value = response.xpath(c["xpath"]).extract()
            if c.has_key("css")  and c["css"]:
                value = response.css(c["css"]).extract()
            if c.has_key("callback") and c["callback"]:
                try:
                    exec c["callback"]
                    ret = callback(value)
                    if ret :
                        value = ret
                except Exception as e:
                    value = None
                    print "callback exec error" , e
                    # raise e
            else:
                if value and len(value) >= 1 :
                    value = value[0]
            infos[name] = value
        item["url"] = response.url.encode('utf-8')
        item["datas"] = infos
        yield item