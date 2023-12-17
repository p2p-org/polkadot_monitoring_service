#!/usr/bin/env python3

import threading
import requests
import yaml
import time
import json
import logging
from collections import deque
from flask import Flask, request, make_response

logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', level=logging.INFO, datefmt='%Y-%m-%d %I:%M:%S')
app = Flask(__name__)

@app.route("/metrics")
def metrics():
    chain = get_config('chain')
    metrics = q_metrics[0].copy()

    out = ""

    try:
        out += '# HELP acala_session_common Common metrics\n'
        out += '# TYPE acala_session_common Common metrics counter\n'

        for k,v in metrics['common'].items():
            out += 'acala_session_common{name="%s",chain="%s"} %s\n' % (k,chain,v)
    except KeyError:
        pass

    try:
        out += '# HELP acala_session_active_validators Active validators\n'
        out += '# TYPE acala_session_active_validators Active validators counter\n'

        for k in metrics['validators'].items():
            out += 'acala_session_active_validators{chain="%s"} %s\n' % (chain,k)
    except KeyError:
        pass

    try:
        out += '# HELP acala_rewards_validator Points earned\n'
        out += '# TYPE acala_rewards_validator Points earned counter\n'

        for k in metrics:
            print (k[validators])
            out += 'acala_rewards_validator{chain="%s" } %s\n' % (chain,k)
    except KeyError:
        pass

    response = make_response(out, 200)
    response.mimetype = "text/plain"

    return response

def api_request(endpoint = "api_substrate",method = None,args = None):
    if endpoint == 'api_substrate':
        url = get_config('api_substrate')

        if isinstance(args, list):
            for i in range(len(args)):
                if isinstance(args[i], str):
                    args[i] = '"' + args[i] + '"'
        elif isinstance(args, str):
            args = '"' + args + '"'
        elif not args:
            args = ""

        data = {'method': method,
                'args': args}

    elif endpoint == 'api_registry':
        url = get_config('api_registry')

        data = {'method': method}

    try:
        r = requests.post(url, json=data)
    except (ConnectionRefusedError,requests.exceptions.ConnectionError):
        logging.critical('Coulnd not get data from ' + endpoint)

        return None

    if r.status_code == 200:
        return r.json()['result']
    else:
        logging.critical('Request to ' + endpoint + ' finished with code ' + str(r.status_code))
        return None

def get_config(part):
    with open('./config.yaml') as config_file:
        data = yaml.load(config_file, Loader=yaml.FullLoader)

    return data[part]

def main():
    block = 0
    session = 0

    while True:
        try:
            last_block = int(api_request(method = 'api.query.system.number'),16)

            if last_block != block:
                validators = api_request(method = 'api.query.session.validators')
                current_session = int(api_request(method = 'api.query.session.currentIndex'),16)
                disabled_validators = api_request(method = 'api.query.session.disabledValidators')
                result = {'validators':{},'common':{}}
                result['common'] = {}
                result['common']['active_validators_count'] = len(validators)
                result['common']['current_session'] = current_session
                for addr in validators: 
                    points = int(api_request(method = 'api.query.collatorSelection.sessionPoints', args = addr),16)
                    validator_points  = {k:points for k in validators if k == addr}
                    result['validators'].update(validator_points)
                             
                q_metrics.clear()
                q_metrics.append(result)
            session = current_session
            block = last_block

        except Exception as e:
            logging.critical(e)
            time.sleep(3)
            continue

        time.sleep(3)

if __name__ == '__main__':
    endpoint_listen = get_config('exporter')['listen']
    endpoint_port = get_config('exporter')['port']

    q_metrics = deque([])

    worker = threading.Thread(target=main)
    worker.daemon = True
    worker.start()

    app.run(host="0.0.0.0", port=int(endpoint_port))
