import logging
import sys
import os
import asyncio
from aiohttp import web
from aiogram import Bot, Dispatcher, Router
from aiogram.fsm.storage.memory import MemoryStorage
from message_handlers.setup import setup_message_handler
from web_apps.setup import setup_web_app
from forms.setup import setup_message_form
from utils.db import DB
from utils.cache import CACHE

logging.basicConfig(level=logging.INFO, stream=sys.stdout)

if __name__ == "__main__":
    admin_chat = os.environ['admin_chat']
    tg_token = os.environ['tg_token']

    db_name = os.environ['db_name']
    db_user = os.environ['db_user']
    db_pass = os.environ['db_pass']
    db_host = os.environ['db_host']
    db_port = os.environ['db_port']

    redis_host = os.environ.get('redis_host', 'redis')
    redis_port = os.environ.get('redis_port', '6379')
    
    grafana_url = os.environ.get('grafana_url', 'http://grafana:3000/d/fDrj0_EGz/p2p-org-polkadot-kusama-dashboard?orgId=1')
    prometheus_alert_path = os.environ.get('prometheus_alert_path', '/prometheus_rules/')
    prometheus_alert_tmpl = os.environ.get('prometheus_alert_tmpl', './alerts_tmpl.yml')
    prometheus_alert_api = os.environ.get('prometheus_alert_api', 'http://prometheus:9090/api/v1/rules')
    prometheus_metric_api = os.environ.get('prometheus_metric_api', 'http://prometheus:9090/api/v1/series')
    prometheus_config_reload = os.environ.get('prometheus_config_reload', 'http://prometheus:9090/-/reload')
    
    cache = CACHE(redis_host, redis_port)
    web_app = web.Application()
    db = DB(db_name, db_user, db_pass,db_host,db_port)
    bot = Bot(token=tg_token, parse_mode="HTML")
    validators_cache = CACHE(redis_host, redis_port)

    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    router = Router()

    dp.include_router(router)

    setup_message_handler('start')

    setup_message_form('support')
    setup_message_form('accounts')

    setup_web_app('ping')
    setup_web_app('prom_alert')
    
    from callback_query_handlers import main_menu, subscribtions, accounts
    from middlewares import acl

    web_runner = web.AppRunner(web_app)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(web_runner.setup())
    
    site = web.TCPSite(web_runner, port=8080)
    loop.run_until_complete(site.start())

    loop.run_until_complete(dp.start_polling(bot))
