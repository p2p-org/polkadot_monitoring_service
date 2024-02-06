from __main__ import prometheus_alert_path, prometheus_alert_tmpl, prometheus_alert_api
import yaml
import json
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

    def _save_yml(self,path,data):
        with open(path, 'w') as file:
            yaml.dump(data, file)

    def list_templates(self):
        rules = self._load_yml(self.prometheus_alert_tmpl)['rules']
       
        return rules

    def get_template(self, uniqueid: int = None):
        rules = self._load_yml(self.prometheus_alert_tmpl)['rules']

        for rule in rules:
            if rule['labels']['uniqueid'] == uniqueid:
                return rule

        return None

    def get_rule(self, uniqueid: int = None):
        try:
            rules = self._load_yml(prometheus_alert_path + '/' + str(self.chat_id) + '.yml')['groups'][0]['rules']
        except (FileNotFoundError, KeyError, IndexError, TypeError):
            return {}

        for rule in rules:
            if rule['labels']['uniqueid'] == uniqueid:
                return rule

        return {}

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
                    t = re.findall(r'\[\[(.*?)\]\]', str(v))
                    append_data(t)
            else:
                t = re.findall(r'\[\[(.*?)\]\]', str(line))
                append_data(t)
         
        return result
        
    def list_alerts(self):
        self.content = requests.get(prometheus_alert_api)

        return self.content.json()

    def add_rule(self, uniqueid: int = None, check_list: Union[dict, str] = None, template: Union[dict, str] = None):
        rule = {}
        
        try:
            self.content = self._load_yml(prometheus_alert_path + '/' + str(self.chat_id) + '.yml')
        except (FileNotFoundError):
            self.content = {'groups':[{'name':'MaaS alert rules set','rules':[]}]}

        try:
            self.content['groups'][0]['rules'] = [ i for i in self.content['groups'][0]['rules'] if int(i['labels']['uniqueid']) != int(uniqueid) ]
        except TypeError:
            self.content = {'groups':[{'name':'MaaS alert rules set','rules':[]}]}
        

        check_list = {k:v['data'] for k,v in check_list.items()}
        check_list['chat_id'] = self.chat_id
        
        template['labels'].update(check_list) 
        check_list['accounts'] = '(' + '|'.join(check_list['accounts']) + ')'

        for label,line in template.items():
            if isinstance(line, dict):
                rule[label] = {}
                for k,v in line.items():
                    if k == 'bot_description':
                        continue
                    if len(re.findall(r'\[\[(.*?)\]\]', str(v))) > 0:
                        rule[label][k] = v.replace('[[','{').replace(']]','}').format(**check_list)
                    else:
                        rule[label][k] = v

            else:
                if len(re.findall(r'\[\[(.*?)\]\]', str(line))) > 0:
                    try:
                        rule[label] = line.replace('[[','{').replace(']]','}').format(**check_list)
                    except ValueError:
                        center = re.findall(r'\{(.*?)\}', str(line))
                        if len(center) > 0:
                            center = center[0]
                            before = line.split('{')[0]
                            after = line.split('}')[1]
                            
                            rule[label] = before.replace('[[','{').replace(']]','}').format(**check_list) + '{' + center.replace('[[','{').replace(']]','}').format(**check_list) + '}' + after.replace('[[','{').replace(']]','}').format(**check_list)
                else:
                    rule[label] = line

        self.content['groups'][0]['rules'].append(rule)

        self._save_yml(prometheus_alert_path + '/' + str(self.chat_id) + '.yml', self.content)

        return self.content

    def delete_rule(self,uniqueid: int = None):
        self.content = self._load_yml(prometheus_alert_path + '/' + str(self.chat_id) + '.yml')

        rules = [ i for i in self.content['groups'][0]['rules'] if int(i['labels']['uniqueid']) != int(uniqueid) ]
        
        self.content['groups'][0]['rules'] = rules

        self._save_yml(prometheus_alert_path + '/' + str(self.chat_id) + '.yml', self.content)

        return self.content
