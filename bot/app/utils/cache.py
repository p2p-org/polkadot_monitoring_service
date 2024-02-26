import logging
import redis

class CACHE():
    def __init__(self, redis_host, redis_port, redis_password=None):
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.redis_password = redis_password

    def connect(self):
        self.r = redis.Redis(host=self.redis_host, port=self.redis_port, password=self.redis_password, db=0)

    def get(self,expr):
        self.connect()
        result = []

        try:
            for key in self.r.scan_iter(expr + "*"):
                result.append(key.decode())

        except redis.exceptions.ConnectionError:
            logging.error("Unable connect to redis.")
            return []

        finally: self.r.close()

        return result

    def count(self):
        self.connect()
        result = []

        try:
            for key in self.r.scan_iter():
                result.append(key.decode())

        except redis.exceptions.ConnectionError:
            logging.error("Unable connect to redis.")
            return len(result)

        finally: self.r.close()

        return len(result)
