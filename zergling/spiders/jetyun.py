# -*- coding: utf-8 -*-

import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import Rule
from scrapy_redis.spiders import RedisCrawlSpider
from scrapy_redis.utils import bytes_to_str
from urlparse import urlparse
from goose import Goose
from goose.text import StopWordsChinese


class JetyunSpider(RedisCrawlSpider):
    name = 'jetyun'

    rules = (
    )

    def make_request_from_data(self, data):
        url = bytes_to_str(data, self.redis_encoding)
        o = urlparse(url)

        extract_links = self.server.smembers(o.netloc+":extracts")
        if extract_links :
            follow_links = self.server.smembers(o.netloc+":follows")
            if follow_links :
                self.rules += (
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
        yield {
            'url': response.url
        }