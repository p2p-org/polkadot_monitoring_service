import requests
import redis
import json
import os
import time
import logging

def cache_is_cold(redis_host,redis_port,redis_password=None):
    r = redis.Redis(host=redis_host, port=redis_port, password=redis_password, db=0)
    return len(r.keys()) == 0

def write_to_cache(redis_host,redis_port,redis_password,data):
    r = redis.Redis(host=redis_host, port=redis_port, password=redis_password, db=0)

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

    redis_host = os.environ.get('redis_host', 'redis')
    redis_port = int(os.environ.get('redis_port', 6379))
    redis_password = os.environ.get('redis_password', None)
    sleep_time = int(os.environ.get('sleep_time', 300))
    prom_label_values_url = os.environ.get('prom_label_values_url', 'http://prometheus:9090/api/v1/label/account/values')

    validators_from_prom = get_from_prom(prom_label_values_url)
    if cache_is_cold(redis_host, redis_port, redis_password):
        validators_from_file = get_from_file('./validators.txt')
    else:
        validators_from_file = []

    data = validators_from_prom
    
    for i in validators_from_file:
        if i not in data:
            data.append(i)

    r = write_to_cache(redis_host,redis_port,redis_password,data)

    if isinstance(r, int):
        logging.info("Total validator accounts in cache " + str(r))

    time.sleep(sleep_time)
