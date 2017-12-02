import logging

from twisted.internet import task

from scrapy.exceptions import NotConfigured
from scrapy import signals
from .itemstatscollector import MemoryItemStatsCollector
import pymongo
import json
import datetime

logger = logging.getLogger(__name__)


class StoreStats(object):
    """Log basic scraping stats periodically"""

    def __init__(self, stats, mongo_uri, mongo_db, collection_name = 'zergling_stats', interval=60.0):
        self.stats = stats
        self.interval = interval
        self.multiplier = 60.0 / self.interval
        self.task = None
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db
        self.collection_name = collection_name

    @classmethod
    def from_crawler(cls, crawler):
        interval = crawler.settings.getfloat('LOGSTATS_INTERVAL')
        mongo_uri = crawler.settings.get('MONGO_URI')
        mongo_db = crawler.settings.get('MONGO_DATABASE', 'items')
        collection_name = "zergling_stats"
        if not interval:
            raise NotConfigured
        o = cls(crawler.stats, mongo_uri, mongo_db, collection_name, interval)
        crawler.signals.connect(o.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(o.spider_closed, signal=signals.spider_closed)
        crawler.signals.connect(o.item_scraped, signal=signals.item_scraped)
        return o

    def spider_opened(self, spider):
        self.pagesprev = 0
        self.itemsprev = 0
        self.itemcollector = MemoryItemStatsCollector()
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]
        self.task = task.LoopingCall(self.store, spider)
        self.task.start(self.interval)

    def item_scraped(self, item, spider):
        if item["website_name"] not in self.itemcollector.item_stats :
            self.itemcollector.new_stats()
            self.itemcollector.set_item_stats(item["website_name"], self.itemcollector.get_stats())
        else:
            self.itemcollector.set_stats(self.itemcollector.item_stats[item["website_name"]])
        self.itemcollector.inc_value(str(datetime.datetime.now().strftime("%Y.%m.%d")), spider=spider)

    def store(self, spider):
        ret = []
        if len(self.itemcollector.item_stats) > 0:
            item_stats_copy = self.itemcollector.item_stats
            self.itemcollector.clear_all()
            for stat in item_stats_copy:
                for p in item_stats_copy[stat]:
                    arr = p.split(".")
                    update = {}
                    field = ""
                    for i in arr:
                        field += str(i)+"."
                        update_inc = update.setdefault("$inc", {})
                        update_inc[field+"i"] = item_stats_copy[stat][p]
                    if update:
                        self.db[self.collection_name].update({"website_name" : stat}, update, upsert=True)

    def spider_closed(self, spider, reason):
        # self.client.close()
        if self.task and self.task.running:
            self.task.stop()
