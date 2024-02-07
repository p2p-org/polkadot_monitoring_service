#!/usr/bin/env python3

import time
import logging
import os
import threading
from collections import deque
from flask import Flask, make_response
from functions import SUBSTRATE_INTERFACE


logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', level=logging.INFO, datefmt='%Y-%m-%d %I:%M:%S')
app = Flask(__name__)


@app.route("/metrics")
def metrics():
    chain = os.environ['CHAIN']

    if len(q_metrics) == 0:
        response = make_response("", 200)
        response.mimetype = "text/plain"

        return response

    metrics = q_metrics[0].copy()

    out = ""

    try:
        out += '# HELP acala_session_common Common metrics\n'
        out += '# TYPE acala_session_common counter\n'

        for k, v in metrics['common'].items():
            out += 'acala_session_common{name="%s", chain="%s"} %s\n' % (k, chain, v)
    except KeyError:
        pass

    try:
        out += '# HELP acala_session_active_validators Active validators\n'
        out += '# TYPE acala_session_active_validators counter\n'

        for k, v in metrics['validators'].items():
            out += 'acala_session_active_validators{chain="%s", account="%s"} %s\n' % (chain, k, v)
    except KeyError:
        pass

    try:
        out += '# HELP acala_rewards_validator Points earned\n'
        out += '# TYPE acala_rewards_validator counter\n'

        for k, v in metrics['validators'].items():
            out += 'acala_rewards_validator{chain="%s", account="%s"} %s\n' % (chain, k, v)
    except KeyError:
        pass

    response = make_response(out, 200)
    response.mimetype = "text/plain"

    return response


def main():
    block = 0

    while True:
        try:
            last_block = substrate_interface.request('System', 'Number').value
            if last_block != block:
                validators = substrate_interface.request('Session', 'Validators').value
                current_session = substrate_interface.request('Session', 'CurrentIndex').value

                result = {'validators': {}, 'common': {}}

                result['common'] = {}
                result['common']['active_validators_count'] = len(validators)
                result['common']['current_session'] = current_session

                for addr in validators:
                    points = substrate_interface.request('CollatorSelection', 'SessionPoints', [addr]).value
                    validator_points = {k: points for k in validators if k == addr}
                    result['validators'].update(validator_points)

                q_metrics.clear()
                q_metrics.append(result)

            block = last_block

        except Exception as e:
            logging.critical(e)
            time.sleep(3)

            continue

        time.sleep(3)


if __name__ == '__main__':
    endpoint_listen = os.environ['LISTEN']
    endpoint_port = os.environ['PORT']
    ws_endpoint = os.environ['WS_ENDPOINT']
    chain = os.environ['CHAIN']

    substrate_interface = SUBSTRATE_INTERFACE(ws_endpoint, chain)

    q_metrics = deque([])

    worker = threading.Thread(target=main)
    worker.daemon = True
    worker.start()

    app.run(host="0.0.0.0", port=int(endpoint_port))
