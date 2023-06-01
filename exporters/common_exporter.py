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
import json
import time
import threading
import logging
import operator
import traceback
from functions import SUBSTRATE_INTERFACE, get_era_points, get_chain_info 
from _thread import interrupt_main
from collections import deque
from flask import Flask, request, make_response
from numpy import median, average, percentile
from decimal import *

logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', level=logging.INFO, datefmt='%Y-%m-%d %I:%M:%S')
app = Flask(__name__)

@app.route('/metrics', methods=['GET'])
def metrics():
    chain = os.environ['CHAIN']
    metrics = q_metrics[0].copy()

    out = ""
   
    try:
        out += '# HELP polkadot_staking_currentEra Current era\n'
        out += '# TYPE polkadot_staking_currentEra counter\n'

        out += 'polkadot_staking_currentEra{chain="%s"} %s\n' % (chain,metrics['common']['currentEra'])

    except KeyError:
        pass

    try:
        out += '# HELP polkadot_staking_eraProgress Era progress\n'
        out += '# TYPE polkadot_staking_eraProgress counter\n'

        out += 'polkadot_staking_eraProgress{chain="%s"} %s\n' % (chain,metrics['common']['eraProgress'])

    except KeyError:
        pass

    try:
        out += '# HELP polkadot_staking_totalPoints Total points\n'
        out += '# TYPE polkadot_staking_totalPoints counter\n'

        out += 'polkadot_staking_totalPoints{chain="%s"} %s\n' % (chain,metrics['totalEraPoints'])

    except KeyError:
        pass

    try:
        out += "# HELP polkadot_staking_eraPoints Validator points\n"
        out += "# TYPE polkadot_staking_eraPoints counter\n"

        for k,v in metrics['eraPoints'].items():
            out += 'polkadot_staking_eraPoints{chain="%s",account="%s"} %s\n' % (chain,k,v)

    except KeyError:
        pass

    try:
        out += "# HELP polkadot_staking_validatorsChart Validators position chart\n"
        out += "# TYPE polkadot_staking_validatorsChart counter\n"

        for k,v in metrics['validatorsChart'].items():
            out += 'polkadot_staking_validatorPositionChart{chain="%s",account="%s"} %s\n' % (chain,k,v)

    except KeyError:
       pass

    try:
        out += '# HELP polkadot_session_currentSession Current session\n'
        out += '# TYPE polkadot_session_currentSession counter\n'

        out += 'polkadot_session_currentSession{chain="%s"} %s\n' % (chain,metrics['common']['currentSession'])

    except KeyError:
        pass

    try:
        out += '# HELP polkadot_session_sessionProgress Session progress\n'
        out += '# TYPE polkadot_session_sessionProgress counter\n'

        out += 'polkadot_session_sessionProgress{chain="%s"} %s\n' % (chain,metrics['common']['sessionProgress'])

    except KeyError:
        pass

    try:
        out += "# HELP polkadot_session_validators Session validators\n"
        out += "# TYPE polkadot_session_validators counter\n"

        for k,v in metrics['sessionValidators'].items():
            out += 'polkadot_session_validators{chain="%s",account="%s"} %s\n' % (chain,k,v)

    except KeyError:
        pass

    try:
        out += '# HELP polkadot_session_paraValidators Active paravalidators\n'
        out += '# TYPE polkadot_session_paraValidators counter\n'

        for k,v in metrics['paraValidators'].items():
            out += 'polkadot_session_paraValidators{chain="%s",account="%s"} %s\n' % (chain,k,v)

    except KeyError:
        pass

    try:
        out += '# HELP polkadot_pv_pointsMedian Points median\n'
        out += '# TYPE polkadot_pv_pointsMedian counter\n'

        out += 'polkadot_pv_pointsMedian{chain="%s"} %s\n' % (chain,metrics['common']['median'])

    except KeyError:
        pass

    try:
        out += '# HELP polkadot_pv_pointsAverage Points average\n'
        out += '# TYPE polkadot_pv_pointsAverage counter\n'

        out += 'polkadot_pv_pointsAverage{chain="%s"} %s\n' % (chain,metrics['common']['average'])

    except KeyError:
        pass
    try:
        out += '# HELP polkadot_pv_pointsP95 Points p95\n'
        out += '# TYPE polkadot_pv_pointsP95 counter\n'

        out += 'polkadot_pv_pointsP95{chain="%s"} %s\n' % (chain,metrics['common']['p95'])

    except KeyError:
        pass

    try:
        out += '# HELP polkadot_pv_eraPoints Our validators\n'
        out += '# TYPE polkadot_pv_eraPoints counter\n'

        for k,v in metrics['pv_eraPoints'].items():
            out += 'polkadot_pv_eraPoints{chain="%s",account="%s"} %s\n' % (chain,k,v)

    except KeyError:
        pass

    try:
        out += "# HELP polkadot_pv_paraValidatorsChart ParaValidators chart\n"
        out += "# TYPE polkadot_pv_paraValidatorsChart counter\n"

        for k,v in metrics['paraValidatorsChart'].items():
            out += 'polkadot_pv_paraValidatorsChart{chain="%s",account="%s"} %s\n' % (chain,k,v)

    except KeyError:
       pass

    response = make_response(out, 200)
    response.mimetype = "text/plain"

    return response

def warmup_state(era,start_session,current_session,session_progress,era_points):
    result_tmp = {}
    result = {}

    if current_session - start_session > 7:
        s_idx = current_session
    else:
        s_idx = start_session

    sessions = []

    while s_idx <= current_session:
        result_tmp[s_idx] = [validator for validator in substrate_interface.request('ParaSessionInfo','AccountKeys',[s_idx]).value]
        sessions.append(s_idx)
        s_idx += 1

    for session,validators in result_tmp.items():
        for i in validators:
            if i not in result.keys():
                result[i] = {}

            result[i][session] = None

    for validator,sessions in result.items():
        full_sessions = len(sessions.keys()) - 1
        divider = full_sessions + (session_progress / 100)

        try:
            points = era_points['result'][validator]
        except KeyError:
            points = 0

        if list(sessions.keys())[-1] == current_session:
            full_session_points = points / divider
            current_session_points = points - (full_session_points * full_sessions)

        elif list(sessions.keys())[-1] != current_session:
            full_session_points = points / len(sessions.keys())

        for k in sessions.keys():
            if k == current_session:
                sessions[k] = int(Decimal(current_session_points))
            elif k != current_session:
                sessions[k] = int(Decimal(full_session_points))

    return result

def calculate_session_points(validator,current_session,era_sessions,era_points):
    state = q_state[0].copy()
    to_delete = []

    if validator not in state.keys():
        state[validator] = {current_session: 0}

    if current_session not in state[validator]:
        state[validator][current_session] = 0

    try:
        total_points = era_points['result'][validator]
    except KeyError:
        total_points = 0

    for session in state[validator].keys():
        if session not in era_sessions:
            to_delete.append(session)

    for session in to_delete:
        del state[validator][session]

    if len(list(state[validator].keys())) == 1:
        points = int(Decimal(total_points))
    else:
        points = int(Decimal(total_points - sum(list(state[validator].values())) + state[validator][current_session]))

    state[validator][current_session] = points

    q_state.clear()
    q_state.append(state)

def construct_metrics(era,current_session,era_progress,session_progress,session_validators,paravalidators,era_points):
    state = q_state[0].copy()
    raw_data = {}
    
    result = {'common':{},'pv_eraPoints':{}}
    result['sessionValidators'] = {k:1 for k in session_validators}
    result['paraValidators'] = {k:1 for k in paravalidators}
    result['eraPoints'] = {k:v for k,v in era_points['result'].items() if k in session_validators}
    result['totalEraPoints'] = era_points['total']

    result['common']['currentEra'] = era
    result['common']['currentSession'] = current_session
    result['common']['eraProgress'] = int(Decimal(era_progress))
    result['common']['sessionProgress'] = int(Decimal(session_progress))

    points_list = []
    
    for validator,sessions in state.items():
        if list(sessions.keys())[-1] == current_session:
            raw_data[validator] = sessions[current_session]
            result['pv_eraPoints'][validator] = sessions[current_session]
            result['paraValidators'][validator] = 1
            points_list.append(sessions[current_session])

    result['common']['median'] = int(Decimal(median(points_list)))
    result['common']['average'] = int(Decimal(average(points_list)))
    result['common']['p95'] = int(Decimal(percentile(points_list,95)))

    result['validatorsChart'] = {k:list(dict(sorted(era_points['result'].items(), key=operator.itemgetter(1),reverse=True)).keys()).index(k) for k in era_points['result'].keys() if k in session_validators}
    result['paraValidatorsChart'] = {k:list(dict(sorted(raw_data.items(), key=operator.itemgetter(1),reverse=True)).keys()).index(k) for k in raw_data.keys() if k in session_validators}

    return result

def main():
    first_iter = True

    while True:
        try:
            chain_info = get_chain_info(chain,substrate_interface)
            era = chain_info['current_era']
            start_session = chain_info['eras_start_session_index']
            current_session = chain_info['current_session']
            era_progress = chain_info['era_progress']
            session_progress = chain_info['session_progress']

            if current_session == start_session:
                era_sessions = [current_session]
            else:
                era_sessions = [i for i in range(start_session,current_session + 1)]
 
            era_points = get_era_points(substrate_interface.request('Staking','ErasRewardPoints',[era]).value)
            session_validators = substrate_interface.request('Session','Validators').value
            paravalidators = substrate_interface.request('ParaSessionInfo','AccountKeys',[current_session]).value

            if first_iter == True:
                q_state.append(warmup_state(era,start_session,current_session,session_progress,era_points))
                first_iter = False

            for validator in paravalidators:
                r = calculate_session_points(validator,current_session,era_sessions,era_points)

            metrics = construct_metrics(era,current_session,era_progress,session_progress,session_validators,paravalidators,era_points)

            q_metrics.clear()
            q_metrics.append(metrics)

        except Exception as e:
            traceback.print_exc()
            interrupt_main()

        time.sleep(15)

if __name__ == '__main__':
    endpoint_listen = os.environ['LISTEN']
    endpoint_port = os.environ['PORT']
    ws_endpoint = os.environ['WS_ENDPOINT']
    chain = os.environ['CHAIN']
 
    substrate_interface = SUBSTRATE_INTERFACE(ws_endpoint,chain)

    q_state = deque([])
    q_metrics = deque([])

    thread = threading.Thread(target=main)
    thread.daemon = True
    thread.start()

    app.run(host=endpoint_listen, port=int(endpoint_port))
