#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Polkadot validator monitoring services.
#
# Copyright 2023 P2P Validator.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import time
import threading
import logging
import traceback
from functions import SUBSTRATE_INTERFACE, get_chain_info, get_keys, ss58_convert
from _thread import interrupt_main
from collections import deque
from flask import Flask, make_response

logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', level=logging.INFO, datefmt='%Y-%m-%d %I:%M:%S')
app = Flask(__name__)


@app.route("/metrics")
def metrics():
    chain = os.environ['CHAIN']

    if len(q_metrics) == 0:
        response = make_response("", 200)
        response.mimetype = "text/plain"

        return response

    metrics = q_metrics[0]

    out = ""

    try:
        out += '# HELP avail_finality_roundsProcessed Blocks processed\n'
        out += '# TYPE avail_finality_roundsProcessed counter\n'

        out += 'avail_finality_roundsProcessed{chain="%s"} %s\n' % (chain, metrics['roundsProcessed'])

    except KeyError:
        pass

    try:
        out += "# HELP avail_finality_prevotes Prevotes\n"
        out += "# TYPE avail_finality_prevotes counter\n"

        for k, v in metrics['validators'].items():
            out += 'avail_finality_prevotes{chain="%s",account="%s"} %s\n' % (chain, k, v['prevotes'])

    except KeyError:
        pass

    try:
        out += "# HELP avail_finality_precommits Precommits\n"
        out += "# TYPE avail_finality_precommits counter\n"

        for k, v in metrics['validators'].items():
            out += 'avail_finality_precommits{chain="%s",account="%s"} %s\n' % (chain, k, v['precommits'])

    except KeyError:
        pass

    response = make_response(out, 200)
    response.mimetype = "text/plain"

    return response


def get_votes(url, substrate_interface):
    rd = 0
    r = {}

    while True:
        try:
            d = substrate_interface.rpc_request(method='grandpa_roundState')
            d = d['result']['best']
            if d['round'] != rd and len(r) != 0:
                q_votes_raw.append(r)

            rd = d['round']
            r = {rd: {}}

            r[rd]['prevotes'] = d['prevotes']['missing']
            r[rd]['precommits'] = d['precommits']['missing']

            if url in q_outaged:
                q_outaged.remove(url)
        except Exception:
            if url not in q_outaged:
                q_outaged.append(url)
            time.sleep(1)
            substrate_interface.connect_websocket()
            pass


def construct_metrics(active_validators, grandpa_keys, votes_threshold, current_session):
    data = q_votes_raw.copy()
    result = {}

    try:
        metrics = q_metrics[0]
    except IndexError:
        metrics = {}
        metrics['currentSession'] = current_session
        metrics['validators'] = {k: {'prevotes': 0, 'precommits': 0} for k in grandpa_keys.keys()}
        metrics['roundsProcessed'] = 0

    try:
        if current_session != metrics['currentSession']:
            logging.info('New session ' + str(current_session) + ' has just begun.')
            metrics['validators'] = {k: {'prevotes': 0, 'precommits': 0} for k in grandpa_keys.keys()}
            metrics['roundsProcessed'] = 0
            metrics['currentSession'] = current_session
    except KeyError:
        pass

    try:
        for i in data:
            for k, v in i.items():
                if k in q_rounds_processed:
                    continue

                prevotes = ss58_convert(v['prevotes'])
                precommits = ss58_convert(v['precommits'])

                try:
                    result[k]['count'] += 1
                except KeyError:
                    result[k] = {'count': 1, 'prevotes': prevotes, 'precommits': precommits}

                if len(prevotes) < len(result[k]['prevotes']):
                    result[k]['prevotes'] = prevotes

                if len(precommits) < len(result[k]['precommits']):
                    result[k]['precommits'] = precommits

                if result[k]['count'] >= votes_threshold:
                    voted_prevotes = []
                    voted_precommits = []

                    for account, params in metrics['validators'].items():
                        if grandpa_keys[account] not in result[k]['prevotes']:
                            voted_prevotes.append(account)
                            params['prevotes'] += 1

                        if grandpa_keys[account] not in result[k]['precommits']:
                            voted_precommits.append(account)
                            params['precommits'] += 1

                    if 'roundsProcessed' not in metrics:
                        metrics['roundsProcessed'] = 1
                    else:
                        metrics['roundsProcessed'] += 1

                    logging.info('Round ' + str(k) + ' has processed. Prevotes: ' + str(len(voted_prevotes)) + '. Precommits:  ' + str(len(voted_precommits)))
                    q_rounds_processed.append(k)

        return metrics
    except RuntimeError as e:
        logging.info('Construct metrics func finished with error ' + str(e))
        pass


def main():
    while True:
        try:
            for i in q_outaged:
                logging.critical('RPC enpdoint ' + i + ' marked as outaged')

            chain_info = get_chain_info(chain, substrate_interface)
            current_session = chain_info['current_session']
            votes_threshold = (rpc_count * thread_count) - (len(q_outaged) * thread_count)
            active_validators = substrate_interface.request('Session', 'Validators').value
            all_keys = substrate_interface.request('Session', 'QueuedKeys').value
            grandpa_keys = get_keys(active_validators, all_keys)

            metrics = construct_metrics(active_validators, grandpa_keys, votes_threshold, current_session)

            q_metrics.clear()
            q_metrics.append(metrics)

        except Exception:
            traceback.print_exc()
            interrupt_main()

        time.sleep(1)


if __name__ == '__main__':
    endpoint_listen = os.environ['LISTEN']
    endpoint_port = os.environ['PORT']
    chain = os.environ['CHAIN']

    rpc_endpoints = os.environ['WS_ENDPOINTS'].split(',')

    threads = []

    rpc_count = len(rpc_endpoints)
    thread_count = 3

    substrate_interface = SUBSTRATE_INTERFACE(rpc_endpoints[0])

    q_metrics = deque([])
    q_votes_raw = deque([], maxlen=rpc_count * thread_count * 15)
    q_rounds_processed = deque([], maxlen=100)
    q_outaged = deque([], maxlen=30)

    for url in rpc_endpoints:
        for i in range(thread_count):
            if url == rpc_endpoints[0]:
                th = threading.Thread(target=get_votes, args=(url, substrate_interface))
            else:
                th = threading.Thread(target=get_votes, args=(url, SUBSTRATE_INTERFACE(url)))
            th.daemon = True
            th.start()
            time.sleep(0.2)

    worker = threading.Thread(target=main)
    worker.daemon = True
    worker.start()

    app.run(host=endpoint_listen, port=int(endpoint_port))
