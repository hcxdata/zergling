# encoding=utf-8
import logging
import redis
from hashlib import md5

from scrapy_redis.dupefilter import RFPDupeFilter
from scrapy_redis.connection import get_redis_from_settings

class SimpleHash(object):
    def __init__(self, cap, seed):
        self.cap = cap
        self.seed = seed

    def hash(self, value):
        ret = 0
        for i in range(len(value)):
            ret += self.seed * ret + ord(value[i])
        return (self.cap - 1) & ret


class BloomFilter(RFPDupeFilter):
    def __init__(self, server=None, key=None, debug=False, db=0, blockNum=1, redis_key='bloomfilter'):
        """
        :param host: the host of Redis
        :param port: the port of Redis
        :param db: witch db in Redis
        :param blockNum: one blockNum for about 90,000,000; if you have more strings for filtering, increase it.
        :param key: the key's name in Redis
        """
        RFPDupeFilter.__init__(self, server, key, debug)
        self.logger = logging.getLogger(__name__)
        # self.server = server
        self.bit_size = 1 << 31  # Redis的String类型最大容量为512M，现使用256M
        self.seeds = [5, 7, 11, 13, 31, 37, 61]
        self.logger.info(self.server)
        self.key = redis_key
        self.blockNum = blockNum
        self.hashfunc = []
        for seed in self.seeds:
            self.hashfunc.append(SimpleHash(self.bit_size, seed))

    @classmethod
    def from_settings(cls, settings, server=None, key=None, debug=None):
        redis_server = get_redis_from_settings(settings)
        debug = settings.getbool('DUPEFILTER_DEBUG')
        redis_db = settings.getint('REDIS_DB')
        redis_blockNum = settings.getint('REDIS_BLOCKNUM')
        redis_key = settings['REDIS_KEY']
        # return cls(redis_server, key=key, debug=debug, db=redis_db, blockNum=redis_blockNum, redis_key=redis_key)
        return cls()

    def isContains(self, str_input):
        if not str_input:
            return False
        m5 = md5()
        m5.update(str_input)
        str_input = m5.hexdigest()
        ret = True
        name = self.key + str(int(str_input[0:2], 16) % self.blockNum)
        for f in self.hashfunc:
            loc = f.hash(str_input)
            ret = ret & self.server.getbit(name, loc)
        return ret

    def insert(self, str_input):
        m5 = md5()
        m5.update(str_input)
        str_input = m5.hexdigest()
        name = self.key + str(int(str_input[0:2], 16) % self.blockNum)
        for f in self.hashfunc:
            loc = f.hash(str_input)
            self.server.setbit(name, loc, 1)

    def request_seen(self, request):
        if self.isContains(request.url): 
            return True
        else:
            self.insert(request.url)