"""
Scrapy extension for collecting scraping stats
"""
import pprint
import logging

logger = logging.getLogger(__name__)


class ItemStatsCollector(object):

    def __init__(self):
        self._stats = {}

    def get_value(self, key, default=None, spider=None):
        return self._stats.get(key, default)

    def get_stats(self, spider=None):
        return self._stats

    def set_value(self, key, value, spider=None):
        self._stats[key] = value

    def set_stats(self, stats, spider=None):
        self._stats = stats

    def inc_value(self, key, count=1, start=0, spider=None):
        d = self._stats
        d[key] = d.setdefault(key, start) + count

    def max_value(self, key, value, spider=None):
        self._stats[key] = max(self._stats.setdefault(key, value), value)

    def min_value(self, key, value, spider=None):
        self._stats[key] = min(self._stats.setdefault(key, value), value)

    def clear_stats(self, spider=None):
        self._stats.clear()

    def new_stats(self, spider=None):
        self._stats = {}

    def copy_stats(self, spider=None):
        return self._stats.copy()

    # def open_spider(self, spider):
    #     pass

    # def close_spider(self, spider, reason):
    #     self._persist_stats(self._stats, spider)

    # def _persist_stats(self, stats, spider):
    #     pass


class MemoryItemStatsCollector(ItemStatsCollector):

    def __init__(self):
        super(MemoryItemStatsCollector, self).__init__()
        self.item_stats = {}

    def set_item_stats(self, key, default=None):
        self.item_stats.setdefault(key, default)

    def clear_all(self):
        self.item_stats = {}


