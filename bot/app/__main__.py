import logging
import sys
import os
import asyncio
from aiogram import Bot,Dispatcher,Router
from aiogram.fsm.storage.memory import MemoryStorage
from message_handlers.setup import setup_message_handler
from web_apps.setup import setup_web_app
from forms.setup import setup_message_form
from callback_data.main import CbData
from aiohttp import web
from utils.db import DB
from utils import subscriptions

logging.basicConfig(level=logging.INFO, stream=sys.stdout)

if __name__ == "__main__":
    admin_chat = os.environ['admin_chat']
    tg_token = os.environ['tg_token']

    db_name = os.environ['db_name']
    db_user = os.environ['db_user']
    db_pass = os.environ['db_pass']
    db_host = os.environ['db_host']
    db_port = os.environ['db_port']
    
    grafana_url = os.environ.get('grafana_url', 'http://127.0.0.1:3000/d/fDrj0_EGz/p2p-org-polkadot-kusama-dashboard?orgId=1')
    prometheus_rules_url = os.environ.get('prometheus_rules_url', 'http://localhost:9090/api/v1/rules')
    prometheus_alert_groups = os.environ.get('prometheus_alert_groups', [])
    if isinstance(prometheus_alert_groups, str):
        prometheus_alert_groups = prometheus_alert_groups.split(',')

    web_app = web.Application()
    db = DB(db_name,db_user,db_pass,db_host,db_port)
    subs = subscriptions.Subscriptions(db, prometheus_rules_url, prometheus_alert_groups)
    bot = Bot(token=tg_token, parse_mode="HTML")

    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    router = Router()
    dp.include_router(router)

    cb = CbData

    setup_message_handler('start')

    setup_message_form('sub_filter')
    setup_message_form('support')

    setup_web_app('ping')
    setup_web_app('prom_alert')
    
    from callback_query_handlers import promalert,main_menu,support,subscriptions

    web_runner = web.AppRunner(web_app)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(web_runner.setup())
    
    site = web.TCPSite(web_runner, port=8080)
    loop.run_until_complete(site.start())

    loop.run_until_complete(dp.start_polling(bot))
