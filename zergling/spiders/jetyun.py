# -*- coding: utf-8 -*-

import copy
import six
import json
import time
import logging
import base64

from urlparse import urlparse
from lxml import etree

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import Rule
from scrapy.http import Request, HtmlResponse

from scrapy_redis.spiders import RedisCrawlSpider
from scrapy_redis.utils import bytes_to_str

from goose import Goose
from goose.text import StopWordsChinese
from ..items import ZerglingItem



logger = logging.getLogger(__name__)

class JetyunSpider(RedisCrawlSpider):
    name = 'jetyun'

    def __init__(self, *a, **kw):
        pass

    def _build_request(self, rule, link, config_json):
        r = Request(url=link.url, callback=self._response_downloaded)
        r.meta.update(rule=rule, link_text=link.text, config_json=config_json)
        return r

    def _requests_to_follow(self, response):
        if not isinstance(response, HtmlResponse):
            return
        seen = set()
        config_json = response.meta.get('config_json', None)
        if not config_json:
            logger.info("response.meta['config_json'] is null =====_requests_to_follow====== %s" %  response.meta)
            return
        else:
            m_rules = self._compile_rules(config_json)
        for n, rule in enumerate(m_rules):
            links = [lnk for lnk in rule.link_extractor.extract_links(response)
                     if lnk not in seen]
            if links and rule.process_links:
                links = rule.process_links(links)
            for link in links:
                seen.add(link)
                r = self._build_request(n, link, config_json)
                yield rule.process_request(r)

    def _response_downloaded(self, response):
        config_json = response.meta.get('config_json', None)
        if config_json:
            m_rules = self._compile_rules(config_json)
            rule = m_rules[response.meta['rule']]
        else:
            logger.info("self._rules: %s============response meta not find rules ,use self._rules=============response.meta: %s" % (self._rules, response.meta))
            return
        return self._parse_response(response, rule.callback, rule.cb_kwargs, rule.follow)

    def make_request_from_data(self, data):
        config_json = json.loads(bytes_to_str(data, self.redis_encoding))
        url = config_json["start_url"]
        r =  self.make_requests_from_url(url)
        r.meta.update(config_json=config_json)
        return r

    def parse_item(self, response):
        g = Goose({'stopwords_class': StopWordsChinese})
        article = g.extract(raw_html=response.body)
        item = ZerglingItem()
        infos = article.infos
        config_json = response.meta.get('config_json', None)
        for k in config_json:
            if k != "collections" and k != "start_url" and k != "extracts" and k != "follows":
                item[k] = config_json[k]
        item["platform"] = 1
        item["url"] = response.url.encode('utf-8')
        collections = config_json["collections"]
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
                    ret = callback(value, item, infos)
                    if ret :
                        value = ret
                except Exception as e:
                    value = None
                    logger.error("callback exec error: %s" % e)
                    # raise e
            else:
                if value and len(value) >= 1 :
                    value = value[0]
            infos[name] = value
        try:
            infos['raw_html'] = base64.b64encode(article.raw_html)
        except Exception as e:
            logger.error("raw_html can't base64 encode, url: %s . error: %s" % (item["url"], e))
        item["datas"] = infos
        item["crawled_at"] = int(time.time())
        logger.info("%s============parse_item=============%s" % (config_json, item["url"]))
        yield item

    def _compile_rules(self, config_json):
        extract_links = config_json["extracts"]
        follow_links = config_json["follows"]
        rules = ()
        if extract_links:
            if follow_links:
                rules +=(
                    Rule(LinkExtractor(allow=( follow_links ))),
                )
            rules += (
                Rule(LinkExtractor(allow=( extract_links )), callback='parse_item'),
            )

        def get_method(method):
            if callable(method):
                return method
            elif isinstance(method, six.string_types):
                return getattr(self, method, None)

        _rules = [copy.copy(r) for r in rules]
        for rule in _rules:
            rule.callback = get_method(rule.callback)
            rule.process_links = get_method(rule.process_links)
            rule.process_request = get_method(rule.process_request)
        return _rules