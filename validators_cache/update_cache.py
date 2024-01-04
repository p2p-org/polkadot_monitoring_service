import requests
import redis
import json
import time
import logging

def write_to_cache(redis_host,redis_port,data):
    r = redis.Redis(host=redis_host, port=redis_port, db=0)

    for key in r.keys():
        r.delete(key)

    for i in data:
        r.set(i,"")
    
    amount = len(r.keys())

    return amount

def get_from_file(path):
    with open(path) as file:
        lines = file.readlines()
        lines = [line.rstrip() for line in lines]

    return lines

def get_from_prom(url):
    r = requests.get(url)
    
    return r.json()['data']

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', level=logging.DEBUG, datefmt='%Y-%m-%d %I:%M:%S')

    validators_from_prom = get_from_prom('http://prometheus:9090/api/v1/label/account/values')
    validators_from_file = get_from_file('./validators.txt')

    data = validators_from_prom
    
    for i in validators_from_file:
        if i not in data:
            data.append(i)

    r = write_to_cache('redis',6379,data)
   
    if isinstance(r, int):
        logging.info("Written validators to cache " + str(r))

    time.sleep(300)
