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
import operator
import traceback
from functions import SUBSTRATE_INTERFACE, get_era_points, get_chain_info
from _thread import interrupt_main
from collections import deque
from flask import Flask, make_response
from numpy import median, average, percentile
from decimal import Decimal

logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', level=logging.INFO, datefmt='%Y-%m-%d %I:%M:%S')
app = Flask(__name__)


@app.route('/metrics', methods=['GET'])
def metrics():
    chain = os.environ['CHAIN']

    if len(q_metrics) == 0:
        response = make_response("", 200)
        response.mimetype = "text/plain"

        return response

    metrics = q_metrics[0].copy()

    out = ""

    try:
        out += '# HELP avail_staking_currentEra Current era\n'
        out += '# TYPE avail_staking_currentEra counter\n'

        out += 'avail_staking_currentEra{chain="%s"} %s\n' % (chain, metrics['common']['currentEra'])

    except KeyError:
        pass

    try:
        out += '# HELP avail_staking_eraProgress Era progress\n'
        out += '# TYPE avail_staking_eraProgress counter\n'

        out += 'avail_staking_eraProgress{chain="%s"} %s\n' % (chain, metrics['common']['eraProgress'])

    except KeyError:
        pass

    try:
        out += '# HELP avail_staking_totalPoints Total points\n'
        out += '# TYPE avail_staking_totalPoints counter\n'

        out += 'avail_staking_totalPoints{chain="%s"} %s\n' % (chain, metrics['totalEraPoints'])

    except KeyError:
        pass

    try:
        out += "# HELP avail_staking_eraPoints Validator points\n"
        out += "# TYPE avail_staking_eraPoints counter\n"

        for k, v in metrics['eraPoints'].items():
            out += 'avail_staking_eraPoints{chain="%s",account="%s"} %s\n' % (chain, k, v)

    except KeyError:
        pass

    try:
        out += "# HELP avail_staking_validatorsChart Validators position chart\n"
        out += "# TYPE avail_staking_validatorsChart counter\n"

        for k, v in metrics['validatorsChart'].items():
            out += 'avail_staking_validatorPositionChart{chain="%s",account="%s"} %s\n' % (chain, k, v)

    except KeyError:
        pass

    try:
        out += "# HELP avail_staking_slashedValidators Unapplied slashes to exact validators\n"
        out += "# TYPE avail_staking_slashedValidators counter\n"

        for k, v in metrics['slashedValidators'].items():
            out += 'avail_staking_slashedValidators{chain="%s", account="%s"} %s\n' % (chain, k, v)

    except KeyError:
        pass

    try:
        out += "# HELP avail_staking_slashedValidatorsCount Count of slashed validators in excat network\n"
        out += "# TYPE avail_staking_slashedValidatorsCount counter\n"

        out += 'avail_staking_slashedValidatorsCount{chain="%s"} %s\n' % (chain, metrics['slashedValidatorsCount'])

    except KeyError:
        pass

    try:
        out += '# HELP avail_session_currentSession Current session\n'
        out += '# TYPE avail_session_currentSession counter\n'

        out += 'avail_session_currentSession{chain="%s"} %s\n' % (chain, metrics['common']['currentSession'])

    except KeyError:
        pass

    try:
        out += '# HELP avail_session_sessionProgress Session progress\n'
        out += '# TYPE avail_session_sessionProgress counter\n'

        out += 'polkadot_session_sessionProgress{chain="%s"} %s\n' % (chain, metrics['common']['sessionProgress'])

    except KeyError:
        pass

    try:
        out += "# HELP avail_session_validators Session validators\n"
        out += "# TYPE avail_session_validators counter\n"

        for k, v in metrics['sessionValidators'].items():
            out += 'avail_session_validators{chain="%s",account="%s"} %s\n' % (chain, k, v)

    except KeyError:
        pass

    response = make_response(out, 200)
    response.mimetype = "text/plain"

    return response


def get_unapplied_slashes(chain, era):
    slashed_validators = []

    max_era = era + 30

    while era < max_era:
        r = substrate_interface.request('Staking', 'UnappliedSlashes', [era]).value

        for i in r:
            slashed_validators.append(i['validator'])

        era = era + 1

    result = {'slashed_validators_count': 0, 'slashed_validators_list': ['null_validator']}

    for i in slashed_validators:
        result['slashed_validators_count'] += 1
        result['slashed_validators_list'].append(i)

    return result


def construct_metrics(era, current_session, era_progress, session_progress, session_validators, slashed_validators, era_points):
    result = {'common': {}}

    result['sessionValidators'] = {k: 1 for k in session_validators}
    result['slashedValidators'] = {k: 1 for k in slashed_validators['slashed_validators_list']}
    result['eraPoints'] = {k: v for k, v in era_points['result'].items() if k in session_validators}
    result['totalEraPoints'] = era_points['total']
    result['slashedValidatorsCount'] = slashed_validators['slashed_validators_count']

    result['common']['currentEra'] = era
    result['common']['currentSession'] = current_session
    result['common']['eraProgress'] = int(Decimal(era_progress))
    result['common']['sessionProgress'] = int(Decimal(session_progress))

    result['common']['median'] = int(Decimal(median(list(result['eraPoints'].values()))))
    result['common']['average'] = int(Decimal(average(list(result['eraPoints'].values()))))
    result['common']['p95'] = int(Decimal(percentile(list(result['eraPoints'].values()), 95)))

    result['validatorsChart'] = {k: list(dict(sorted(era_points['result'].items(), key=operator.itemgetter(1), reverse=True)).keys()).index(k) for k in era_points['result'].keys() if k in session_validators}

    return result


def main():
    while True:
        try:
            chain_info = get_chain_info(chain, substrate_interface)
            era = chain_info['current_era']
            current_session = chain_info['current_session']
            era_progress = chain_info['era_progress']
            session_progress = chain_info['session_progress']

            era_points = get_era_points(substrate_interface.request('Staking', 'ErasRewardPoints', [era]).value)
            session_validators = substrate_interface.request('Session', 'Validators').value
            slashed_validators = get_unapplied_slashes(chain, era)

            metrics = construct_metrics(era, current_session, era_progress, session_progress, session_validators, slashed_validators, era_points)

            q_metrics.clear()
            q_metrics.append(metrics)

        except Exception:
            traceback.print_exc()
            interrupt_main()

        time.sleep(15)


if __name__ == '__main__':
    endpoint_listen = os.environ['LISTEN']
    endpoint_port = os.environ['PORT']
    ws_endpoint = os.environ['WS_ENDPOINT']
    chain = os.environ['CHAIN']

    substrate_interface = SUBSTRATE_INTERFACE(ws_endpoint)

    q_state = deque([])
    q_metrics = deque([])

    thread = threading.Thread(target=main)
    thread.daemon = True
    thread.start()

    app.run(host=endpoint_listen, port=int(endpoint_port))
