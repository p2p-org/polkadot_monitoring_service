#!/usr/bin/env python3

import threading
import requests
import yaml
import time
import json
import logging
from numpy import median, average, percentile
from decimal import *
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
        out += '# HELP astar_currentEra Current era\n'
        out += '# TYPE astar_currentEra Current era counter\n'

        out += 'astar_currentEra{chain="%s"} %s\n' % (chain,metrics['common']['current_era'])
    except KeyError:
        pass

    try:
        out += '# HELP astar_currentSession Current session\n'
        out += '# TYPE astar_currentSession Current session counter\n'

        out += 'astar_currentSession{chain="%s"} %s\n' % (chain,metrics['common']['current_session'])
    except KeyError:
        pass

    try:
        out += '# HELP astar_activeCollatorsCount Active collators\n'
        out += '# TYPE astar_activeCollatorsCount Active collators counter\n'

        out += 'astar_activeCollatorsCount{chain="%s"} %s\n' % (chain,metrics['common']['active_collators_count'])
    except KeyError:
        pass

    try:
        out += '# HELP astar_sessionBlocks Session blocks\n'
        out += '# TYPE astar_sessionBlocks Session blocks counter\n'

        out += 'astar_sessionBlocks{chain="%s"} %s\n' % (chain,metrics['common']['session_blocks'])
    except KeyError:
        pass

    try:
        out += '# HELP astar_blocksAvg Blocks avarage\n'
        out += '# TYPE astar_blocksAvg Blocks avarage counter\n'

        out += 'astar_blocksAvg{chain="%s"} %s\n' % (chain,metrics['common']['average'])
    except KeyError:
        pass

    try:
        out += '# HELP astar_blocksMedian Blocks median\n'
        out += '# TYPE astar_blocksMedian Blocks median counter\n'

        out += 'astar_blocksMedian{chain="%s"} %s\n' % (chain,metrics['common']['median'])
    except KeyError:
        pass

    try:
        out += '# HELP astar_blocksP95 Blocks p95\n'
        out += '# TYPE astar_blocksP95 Blocks p95 counter\n'

        out += 'astar_blocksP95{chain="%s"} %s\n' % (chain,metrics['common']['p95'])
    except KeyError:
        pass

    try:
        out += '# HELP astar_activeCollators Active collators\n'
        out += '# TYPE astar_activeCollators Active collators counter\n'
   
        for k,v in metrics['collators'].items():
            
            out += 'astar_activeCollators{node="%s",chain="%s",account="%s"} %s\n' % (v['node'],chain,k,v['is_active'])
            
    except KeyError:
        pass

    try:
        out += '# HELP astar_blockAuthorship Blocks authored\n'
        out += '# TYPE astar_blockAuthorship Blocks authored counter\n'

        for k,v in metrics['collators'].items():
            out += 'astar_blockAuthorship{node="%s",chain="%s",account="%s"} %s\n' % (v['node'],chain,k,v['authored_blocks_count'])
    except KeyError:
        pass


    response = make_response(out, 200)
    response.mimetype = "text/plain"

    return response

def api_request(method = None,args = None):
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

    try:
        r = requests.post(url, json=data)
    except (ConnectionRefusedError,requests.exceptions.ConnectionError) as e:
        logging.critical(e)
        return None

    if r.status_code == 200:
        return r.json()['result']
    else:
        logging.critical('Request to ' + url + ' finished with code ' + str(r.status_code))
        return None

def get_config(part):
    with open('./config.yaml') as config_file:
        data = yaml.load(config_file, Loader=yaml.FullLoader)
   
    return data[part]

def get_block_count(addr):
    try:
        authored_block = int(api_request(method = 'api.query.collatorSelection.lastAuthoredBlock', args = addr),16)
        
        for i in q_collators:
            idx = q_collators.index(i)
            if addr in i.keys():
                if authored_block not in q_collators[idx][addr]:
                    q_collators[idx][addr].append(authored_block)
                
    except Exception as e:
        logging.critical('The collators thread been stucked with error "' + str(e) + '"')

def main():
    block = 0
    era = 0
    session = 0

    while True:
        try:
            current_era = int(api_request(method = 'api.query.dappsStaking.currentEra')[2:],16)
            current_session = int(api_request(method = 'api.query.session.currentIndex')[2:],16)
            
            if era != current_era:
                logging.info('New era ' + str(current_era) + ' has just begun')

            if session != current_session:
                processed = []
                q_collators.clear()
                active_collators = api_request(method = 'api.query.session.validators')
                disabled_collators = api_request(method = 'api.query.session.disabledValidators')
                
                for addr in active_collators:
                    if addr not in collators.keys() and addr not in processed:
                        q_collators.append({addr:[]})
                        processed.append(addr)
                
                for k,v in collators.items():
                     if v in active_collators:
                        collator_idx = active_collators.index(k)
                        v['authored_blocks_count'] = 0
                        v['is_active'] = 1
                        result = {'collators':collators, 'common':{}}
                     else:
                        result = {'collators':{}, 'common':{}}
                        v['is_active'] = 0
                        break
 
                result['common']['current_era'] = current_era
                result['common']['current_session'] = current_session
                result['common']['session_blocks'] = 0
                logging.info('New session ' + str(current_session) + ' has just begun')

            last_block = int(api_request(method = 'api.query.system.number'),16)
       
            if last_block != block:
                logging.info('Processing block ' + str(last_block))
        
                blocks_per_collator = []
                if result['collators'].items():                
                   for addr,params in result['collators'].items():

                        if addr in active_collators:
                           authored_block = api_request(method = 'api.query.collatorSelection.lastAuthoredBlock', args = addr)
                           authored_block = int(authored_block, 16)
         
                        if 'last_authored_block' not in params:
                           params['last_authored_block'] = authored_block

                        if params['last_authored_block'] != authored_block:
                           params['authored_blocks_count'] += 1
                           logging.info('Collator ' + str(addr) + ' has just constructed block ' + str(authored_block))
                
                        params['last_authored_block'] = authored_block
                
                threads = []
                
                for addr in active_collators:
                    if addr not in collators.keys():
                        th = threading.Thread(target=get_block_count,args=(addr,))
                        threads.append(th)

                for t in threads:
                    t.start()
                    t.join()
                
                for c in q_collators:
                    blocks_per_collator.append(len(list(c.values())[0]))

                result['common']['session_blocks'] += 1
                result['common']['median'] = int(Decimal(median(blocks_per_collator)))
                result['common']['average'] = int(Decimal(average(blocks_per_collator)))
                result['common']['p95'] = int(Decimal(percentile(blocks_per_collator,95)))

                q_metrics.clear()
                q_metrics.append(result)

            era = current_era
            session = current_session
            block = last_block

        except Exception as e:
            logging.critical('The main thread been stucked with error "' + str(e) + '"')
            time.sleep(10)
            continue
        
        time.sleep(3)

if __name__ == '__main__':
    endpoint_listen = get_config('exporter')['listen']
    endpoint_port = get_config('exporter')['port']
  
    collators = {}

    for k,v in get_config('validators').items():
        collators[v['account']] = {'node':k}

    q_metrics = deque([])
    q_collators = deque([])

    worker = threading.Thread(target=main)
    worker.daemon = True
    worker.start()

    app.run(host="0.0.0.0", port=int(endpoint_port))