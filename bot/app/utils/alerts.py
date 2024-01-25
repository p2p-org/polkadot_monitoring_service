from __main__ import prometheus_alert_path, prometheus_alert_tmpl, prometheus_alert_api
import yaml
import requests
import re 
from typing import Union

class Alerts():
    def __init__(self,chat_id: int):
        self.prometheus_alert_path = prometheus_alert_path
        self.prometheus_alert_tmpl = prometheus_alert_tmpl
        self.chat_id = chat_id

    def _load_yml(self,path):
        with open(path) as file:
            return yaml.load(file, Loader=yaml.FullLoader)

    def _save_yaml(self,path,data):
        with open(path, 'w') as file:
            yaml.dump(data, path)

    def list_templates(self):
        rules = self._load_yml(self.prometheus_alert_tmpl)['rules']
       
        return rules

    def get_template(self, uniqueid: int = None):
        rules = self._load_yml(self.prometheus_alert_tmpl)['rules']

        for rule in rules:
            if rule['labels']['uniqueid'] == uniqueid:
                return rule

        return None

    def get_variables(self, template: Union[dict, str] = None, uniqueid: int = None):
        def append_data(data):
            try:
                for i in data:
                    if i not in result:
                        result.append(i)
            except IndexError:
                pass

        result = []
        
        if not template:
            template = self.get_template(uniqueid)
        
        for line in template.values():
            if isinstance(line, dict):
                for v in line.values():
                    t = re.findall(r'\%(.*?)\%', str(v))
                    append_data(t)
            
            t = re.findall(r'\%(.*?)\%', str(line))
            append_data(t)

        return result
        
    def list_alerts(self):
        self.content = requests.get(prometheus_alert_api)

        return self.content.json()

    def create(self, uniqueid: int):
        self.content = get_template(uniqueid)

        return content
