
from utils.db import DB
import asyncio, aiohttp

class Alert():
    def __init__(self, prom_json: dict) -> None:
        alert = prom_json.get('alerts', [{}])[0]

        labels = alert.get('labels', {})
        annotations = alert.get('annotations', {})

        self.alertname = labels.get('alertname', '')
        self.severity = labels.get('severity', '')
        self.description = annotations.get('description', '')

        self.kv = {'alertname': self.alertname}
        for k, v in annotations.items():
            if k not in ['description', 'summary']:
                self.kv[k] = v

class AlertRule:
    def __init__(self, prom_rule: dict) -> None:
        self.severity = prom_rule.get("labels", {}).get("severity", "info")
        self.alertname = prom_rule.get("name")
        annotations = prom_rule.get('annotations', {})
        # save all possible annotation names exluding desc and summary
        # eg: account, event_type, etc...
        self.keys = [k for k in annotations if k not in ['description', 'summary']]

    
    def __gt__(self, other):
        return self.alertname > other.alertname

    def dict(self):
        d = dict()
        d['alertname'] = [self.alertname]
        for k in self.keys:
            d[k] = ['any']
        return d

class AlertRules:
    def __init__(self, prom_resp: dict, only_groups: [str] = []) -> None:
        self.rules = dict()
        self.only_groups = only_groups

        # # successful resp sample
        # status: "success"
        # data: 
        # - groups:
        #   - name: ""
        #     rules:
        #     - name: ""
        #       annotations: {}
        #       labels: {}
        if prom_resp.get("status", "") != "success":
            raise Exception("unable to get 200 response from Prometheus API")        
        for group in prom_resp.get("data", {}).get("groups", []):
            if self.only_groups == [] or group.get('name', '') in self.only_groups:
                for rule in group.get("rules", []):
                    self.add(rule)

    def add(self, prom_rule: dict) -> AlertRule:
        r = AlertRule(prom_rule)
        self.rules[r.alertname] = r
        return r
    
    def list(self) -> list[AlertRule]:
        return sorted(self.rules.values())

    def by_name(self, name) -> AlertRule:
        try:
            return self.rules[name]
        except KeyError:
            return None

class Subscriptions:
    def __init__(self, db: DB, rules_url: str, only_groups: list[str]=[]):
        self.db = db
        self.rules_url = rules_url
        self.only_groups = only_groups

    async def get_rule_by_name(self, name: str) -> AlertRule:
        rules = await self.get_rules()
        return rules.by_name(name)
        
    async def get_rules(self) -> AlertRules:
        e = None
        for i in range(1, 10):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(self.rules_url) as r:
                        resp = await r.json()
                break
            except Exception as err:
                e = err
                await asyncio.sleep(10)

        if e != None:
            raise(Exception("unable to read data from Prometheus API {0}, reason: {1}".format(self.rules_url, str(e))))
    
        return AlertRules(prom_resp=resp, only_groups=self.only_groups)
    
    def user_subscribe(self, chat_id: int, subscription_name: str, lvs: dict[str, any]):
        return self.db.add_or_update_subscription(chat_id, subscription_name, lvs)

    def must_notify(self, chat_id, a: Alert):
        subs = self.get_subscriptions(chat_id)

        for filters in subs.values():
            matched = []
            for key, values in filters.items():
                for val in values:
                    if a.kv.get(key, '') == val or val == 'any':
                        matched.append(True)
            if len(matched) == len(filters):
                return True
        return False
        
    def user_unsubscribe(self, chat_id: int, subscription_name: str):
        self.db.delete_subscription(chat_id, subscription_name)

    def get_subscriptions(self, chat_id: int):
        if chat_id == 0:
            return {}
        db_subs = self.db.get_subscriptions(chat_id)
        subs = {}
        for sub in db_subs:
            subscription_name = sub.get('subscription_name')
            if subs.get(subscription_name) == None:
                subs[subscription_name] = {}
            key = sub.get('key_name')
            value = sub.get('key_value')
            if subs[subscription_name].get(key) == None:
                subs[subscription_name][key] = [value]
            else:
                subs[subscription_name][key].append(value)
        return subs
    
    def get_subscription_by_index(self, chat_id: int, index: int):
        subs = self.get_subscriptions(chat_id=chat_id)
        keys = sorted(subs.keys())
        if index >= 0 and index < len(keys) and len(keys) >= 1:
            return subs[keys[index]], len(keys)
