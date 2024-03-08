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
        out += '# HELP acala_currentSession Current session\n'
        out += '# TYPE acala_currentSession counter\n'

        out += 'acala_currentSession{chain="%s"} %s\n' % (chain, metrics['common']['current_session'])
    except KeyError:
        pass

    try:
        out += '# HELP acala_activeCollators Active collators\n'
        out += '# TYPE acala_activeCollators counter\n'

        for i in metrics['collators'].keys():
            out += 'acala_activeCollators{chain="%s", account="%s"} 1\n' % (chain, i)
    except KeyError:
        pass

    try:
        out += '# HELP acala_sessionPoints Points earned\n'
        out += '# TYPE acala_sessionPoints counter\n'

        for k, v in metrics['collators'].items():
            out += 'acala_sessionPoints{chain="%s", account="%s"} %s\n' % (chain, k, v)
    except KeyError:
        pass

    response = make_response(out, 200)
    response.mimetype = "text/plain"

    return response


def main():
    session = 0

    while True:
        try:
            current_session = substrate_interface.request('Session', 'CurrentIndex').value

            if session != current_session:
                active_collators = substrate_interface.request('Session', 'Validators').value
                result = {'collators': {}, 'common': {}}

                result['common'] = {}
                result['common']['current_session'] = current_session

                logging.info('New session ' + str(current_session) + ' has just begun')

            for addr in active_collators:
                result['collators'][addr] = substrate_interface.request('CollatorSelection', 'SessionPoints', [addr]).value

            q_metrics.clear()
            q_metrics.append(result)

            session = current_session

        except Exception as e:
            logging.critical('The main thread been stucked with error "' + str(e) + '"')
            time.sleep(10)

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
