import logging
import redis

class CACHE():
    def __init__(self, redis_host, redis_port):
        self.redis_host = redis_host
        self.redis_port = redis_port

    def connect(self):
        self.r = redis.Redis(host=self.redis_host, port=self.redis_port, password=self.redis_pass, db=0)

    def list(self,expr):
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
