#!/usr/bin/env python3

import threading
import time
import logging
import os
from numpy import median, average, percentile
from collections import deque
from flask import Flask, make_response
from decimal import Decimal
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
        out += '# HELP manta_currentRound Current round\n'
        out += '# TYPE manta_round Current round counter\n'

        out += 'manta_currentRound{chain="%s"} %s\n' % (chain, metrics['common']['current_round'])
    except KeyError:
        pass

    try:
        out += '# HELP manta_activeCollatorsCount Active collators\n'
        out += '# TYPE manta_activeCollatorsCount Active collators counter\n'

        out += 'manta_activeCollatorsCount{chain="%s"} %s\n' % (chain, metrics['common']['active_collators'])
    except KeyError:
        pass

    try:
        out += '# HELP manta_roundBlocks Round blocks\n'
        out += '# TYPE manta_roundBlocks Round blocks counter\n'

        out += 'manta_roundBlocks{chain="%s"} %s\n' % (chain, metrics['common']['rnd_blocks'])
    except KeyError:
        pass

    try:
        out += '# HELP manta_blocksAvg Blocks avarage\n'
        out += '# TYPE manta_blocksAvg Blocks avarage counter\n'

        out += 'manta_blocksAvg{chain="%s"} %s\n' % (chain, metrics['common']['average'])
    except KeyError:
        pass

    try:
        out += '# HELP manta_blocksMedian Blocks median\n'
        out += '# TYPE manta_blocksMedian Blocks median counter\n'

        out += 'manta_blocksMedian{chain="%s"} %s\n' % (chain, metrics['common']['median'])
    except KeyError:
        pass

    try:
        out += '# HELP manta_blocksP95 Blocks p95\n'
        out += '# TYPE manta_blocksP95 Blocks p95 counter\n'

        out += 'manta_blocksP95{chain="%s"} %s\n' % (chain, metrics['common']['p95'])
    except KeyError:
        pass

    try:
        out += '# HELP manta_activeCollators Active collator\n'
        out += '# TYPE manta_activeCollators Active collator counter\n'

        for k, v in metrics['collators'].items():
            out += 'manta_activeCollators{chain="%s", account="%s"} %s\n' % (chain, k, v['is_active'])
    except KeyError:
        pass

    try:
        out += '# HELP manta_blockAuthorship Block authors\n'
        out += '# TYPE manta_blockAuthorship Block authors counter\n'

        for k, v in metrics['collators'].items():
            out += 'manta_blockAuthorship{chain="%s", account="%s"} %s\n' % (chain, k, v['authored_blocks_count'])
    except KeyError:
        pass

    response = make_response(out, 200)
    response.mimetype = "text/plain"

    return response


def main():
    block = 0
    rnd = 0

    while True:
        try:
            current_rnd = substrate_interface.request('ParachainStakin', 'Round').value['current']

            if current_rnd != rnd:
                collators = substrate_interface.request('ParachainStaking', 'SelectedCandidates').value
                active_collators = substrate_interface.request('ParachainStaking', 'SelectedCandidates').value

                common = {}
                common['current_round'] = current_rnd
                common['rnd_blocks'] = 0

                result = {'collators': {}, 'common': {'current_round': current_rnd, 'rnd_blocks': 0}}
                result['collators'] = {i['owner']: {'is_active': 0, 'authored_blocks_count': 0} for i in collators}

                for k, v in result['collators'].items():
                    if k in active_collators:
                        v['is_active'] = 1

                logging.info('New round ' + str(current_rnd) + ' has just begun')

            last_block = int(substrate_interface.request('System', 'Number').value, 16)

            if last_block != block:
                logging.info('Processing block ' + str(last_block))

                block_author = substrate_interface.request('AuthorInherent', 'Author').value

                if block_author in result['collators'].keys():
                    result['collators'][block_author]['authored_blocks_count'] += 1
                    logging.info('Collator ' + str(block_author) + ' has just constructed block ' + str(last_block))

                result['common']['rnd_blocks'] += 1

                result['common']['median'] = int(Decimal(median(list(result['collators'].values()))))
                result['common']['average'] = int(Decimal(average(list(result['collators'].values()))))
                result['common']['p95'] = int(Decimal(percentile(list(result['collators'].values()), 95)))

                q_metrics.clear()
                q_metrics.append(result)

            rnd = current_rnd
            block = last_block

        except Exception as e:
            logging.critical('The main thread been stucked with error "' + str(e) + '"')
            time.sleep(5)

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
