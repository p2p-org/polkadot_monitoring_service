#!/usr/bin/env python3
import os
import threading
import time
import logging
from collections import deque
from functions import SUBSTRATE_INTERFACE
from flask import Flask, make_response

logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', level=logging.INFO, datefmt='%Y-%m-%d %I:%M:%S')
app = Flask(__name__)


@app.route("/metrics")
def metrics():
    metrics = q_metrics[0].copy()

    out = ""

    try:
        out += '# HELP astar_currentSession Current session\n'
        out += '# TYPE astar_currentSession counter\n'

        out += 'astar_currentSession{chain="%s"} %s\n' % (chain, metrics['common']['current_session'])
    except KeyError:
        pass

    try:
        out += '# HELP astar_activeCollators Active collators\n'
        out += '# TYPE astar_activeCollators counter\n'

        for i in metrics['collators'].keys():
            out += 'astar_activeCollators{chain="%s", account="%s"} 1\n' % (chain, i)

    except KeyError:
        pass

    try:
        out += '# HELP astar_sessionBlocks Session blocks\n'
        out += '# TYPE astar_sessionBlocks counter\n'

        out += 'astar_sessionBlocks{chain="%s"} %s\n' % (chain, metrics['common']['session_blocks'])
    except KeyError:
        pass

    try:
        out += '# HELP astar_blockAuthorship Blocks authored\n'
        out += '# TYPE astar_blockAuthorship counter\n'

        for k, v in metrics['collators'].items():
            out += 'astar_blockAuthorship{chain="%s", account="%s"} %s\n' % (chain, k, v['authored_blocks_count'])
    except KeyError:
        pass

    response = make_response(out, 200)
    response.mimetype = "text/plain"

    return response


def main():
    block = 0
    session = 0

    while True:
        try:
            current_session = int(substrate_interface.request('Session', 'CurrentIndex').value)

            if session != current_session:
                active_collators = substrate_interface.request('Session', 'Validators').value
                result = {'collators': {}, 'common': {}}

                for addr in active_collators:
                    result['collators'][addr] = {'is_active': 0, 'authored_blocks_count': 0}

                result['common']['current_session'] = current_session
                result['common']['session_blocks'] = 0

                logging.info('New session ' + str(current_session) + ' has just begun')

            last_block = substrate_interface.request('System', 'Number').value

            if last_block != block:
                logging.info('Processing block ' + str(last_block))

                for addr, params in result['collators'].items():
                    authored_block = substrate_interface.request('CollatorSelection', 'LastAuthoredBlock', [addr]).value

                    if 'last_authored_block' not in params.keys():
                        params['last_authored_block'] = authored_block

                        continue

                    if authored_block == last_block:
                        params['authored_blocks_count'] += 1
                        params['last_authored_block'] = authored_block

                        logging.info('Collator ' + str(addr) + ' has just constructed block ' + str(authored_block))

                result['common']['session_blocks'] += 1

                q_metrics.clear()
                q_metrics.append(result)

            session = current_session
            block = last_block

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

    substrate_interface = SUBSTRATE_INTERFACE(ws_endpoint)

    q_metrics = deque([])

    worker = threading.Thread(target=main)
    worker.daemon = True
    worker.start()

    app.run(host="0.0.0.0", port=int(endpoint_port))
