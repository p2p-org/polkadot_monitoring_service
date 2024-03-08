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

import logging
from substrateinterface import SubstrateInterface, Keypair
from substrateinterface.exceptions import SubstrateRequestException
from websocket._exceptions import WebSocketConnectionClosedException


class SUBSTRATE_INTERFACE:
    def __init__(self, ws_endpoint):
        self.substrate = SubstrateInterface(
            url=ws_endpoint,
            ss58_format=42)

    def request(self, module: str, function: str, params: str = None):
        try:
            r = self.substrate.query(
                module=module,
                storage_function=function,
                params=params)

            return r
        except (WebSocketConnectionClosedException, ConnectionRefusedError, SubstrateRequestException) as e:
            self.substrate.connect_websocket()
            logging.critical('The substrate api call failed with error ' + str(e))
            r = None

    def rpc_request(self, method: str, params: str = None):
        return self.substrate.rpc_request(method=method, params=params)


def get_era_points(data):
    result = {}

    for i in data['individual']:
        result[i[0]] = i[1]

    return {'result': result, 'total': data['total']}


def get_chain_info(chain, substrate_interface):
    constants = {
        'polkadot': {'session_length': 2400, 'era_length': 14400},
        'kusama': {'session_length': 600, 'era_length': 3600}
    }

    session_length = constants[chain]['session_length']
    era_length = constants[chain]['era_length']

    current_era = substrate_interface.request('Staking', 'ActiveEra').value['index']
    current_session = substrate_interface.request('Session', 'CurrentIndex').value

    eras_start_session_index = substrate_interface.request('Staking', 'ErasStartSessionIndex', [current_era]).value

    genesis_slot = substrate_interface.request('Babe', 'GenesisSlot').value
    current_slot = substrate_interface.request('Babe', 'CurrentSlot').value

    session_start_slot = int(current_session) * int(session_length) + int(genesis_slot)
    session_progress = int(current_slot) - int(session_start_slot)

    era_session_index = int(current_session) - int(eras_start_session_index)
    era_progress = int(era_session_index) * int(session_length) + int(session_progress)

    return {'current_era': current_era, 'eras_start_session_index': eras_start_session_index, 'current_session': current_session, 'era_progress': era_progress / era_length * 100, 'session_progress': session_progress / session_length * 100}


def ss58_convert(data):
    r = []

    for key in data:
        pubkey = Keypair(ss58_address=key).public_key.hex()
        r.append('0x' + pubkey)

    return r


def get_keys(validators, keys):
    result = {i: None for i in validators}

    for i in keys:
        if str(i[0]) in result.keys():
            result[str(i[0])] = str(i[1]['grandpa'])

    return result
