from collections import deque
from flask import Flask, make_response
import threading
import requests
import time
import datetime
import yaml
import logging
import os

logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', level=logging.INFO, datefmt='%Y-%m-%d %I:%M:%S')
app = Flask(__name__)


@app.route("/metrics")
def metrics():
    if len(q_metrics) == 0:
        response = make_response("", 200)
        response.mimetype = "text/plain"

        return response

    metrics = q_metrics[0].copy()

    try:
        out = '# HELP github_latest_release_seconds Seconds from latest release\n'
        out += '# TYPE github_latest_release_seconds gauge\n'

        for k, v in metrics.items():
            out += 'github_latest_release_seconds{project="%s"} %s\n' % (k, v)

    except KeyError:
        pass

    response = make_response(out, 200)
    response.mimetype = "text/plain"

    return response


def load_yml(path):
    with open(path) as file:
        return yaml.load(file, Loader=yaml.FullLoader)


def main():
    result = {}

    while True:
        try:
            for name, url in projects['projects'].items():
                try:
                    current_ts = datetime.datetime.now().timestamp()
                    date_str = requests.get(url).json()['published_at']
                    release_ts = time.mktime(datetime.datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ").timetuple())
                    result[name] = str(current_ts - release_ts).split('.')[0]

                except KeyError:
                    continue

            q_metrics.clear()
            q_metrics.append(result)

            time.sleep(120)

        except Exception as e:
            logging.critical('The main thread been stucked with error "' + str(e) + '"')
            time.sleep(5)

            continue


if __name__ == '__main__':
    endpoint_listen = os.environ['LISTEN']
    endpoint_port = os.environ['PORT']

    projects = load_yml('./projects.yml')

    q_metrics = deque([])

    worker = threading.Thread(target=main)
    worker.start()

    app.run(host=endpoint_listen, port=int(endpoint_port))
