import logging
import sys
import os
import asyncio
from aiogram import Bot, Dispatcher, Router
from aiogram.fsm.storage.memory import MemoryStorage
#from aiogram.utils import executor
from message_handlers.setup import setup_message_handler
from web_apps.setup import setup_web_app
from forms.setup import setup_message_form
from callback_data.main import Cb
from aiohttp import web
from db import DB
import time 
logging.basicConfig(level=logging.INFO, stream=sys.stdout)

if __name__ == "__main__":
    admin_chat = os.environ['admin_chat']
    tg_token = os.environ['tg_token']

    db_name = os.environ['db_name']
    db_user = os.environ['db_user']
    db_pass = os.environ['db_pass']
    db_host = os.environ['db_host']
    db_port = os.environ['db_port']
    
    run_mode = os.environ.get('run_mode', 'standalone')

    #loop = asyncio.get_event_loop()
    loop = asyncio.get_event_loop()
    storage = MemoryStorage()
    #bot = Bot(token=tg_token, loop=loop, parse_mode="HTML")
    bot = Bot(token=tg_token, parse_mode="HTML")
    #dp = Dispatcher(bot, storage=storage)
    dp = Dispatcher(storage=storage)
    router = Router()
    dp.include_router(router)
    web_app = web.Application()
    db = DB(db_name,db_user,db_pass,db_host,db_port)

    bot = Bot(token=tg_token, parse_mode="HTML")

    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    router = Router()
    dp.include_router(router)

    cb = Cb

    setup_message_handler('start')
#    setup_message_handler('support')

#    setup_message_form('support')

    setup_web_app('ping')
    setup_web_app('prom_alert')
    
    from callback_query_handlers import promalert,main_menu,grafana,support

    web_runner = web.AppRunner(web_app)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(web_runner.setup())
    
    site = web.TCPSite(web_runner, port=8080)
    loop.run_until_complete(site.start())
    #executor.start_polling(dp, skip_updates=True)
#    dp.run_polling(bot)
