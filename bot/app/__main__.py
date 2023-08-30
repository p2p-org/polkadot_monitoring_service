import logging
import sys
import os
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor
from handlers.setup import setup_message_handler
from web_apps.setup import setup_web_app
from aiohttp import web
from db import DB

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

    loop = asyncio.get_event_loop()
    storage = MemoryStorage()
    bot = Bot(token=tg_token, loop=loop, parse_mode="HTML")
    dp = Dispatcher(bot, storage=storage)
    web_app = web.Application()
    db = DB(db_name,db_user,db_pass,db_host,db_port)

    setup_message_handler('start')
    setup_message_handler('build')
    setup_message_handler('destroy')
    setup_message_handler('support')
    setup_message_handler('ban')
    setup_message_handler('unban')
    setup_message_handler('promalert')

    setup_web_app('ping')
    setup_web_app('prom_alert')

    runner = web.AppRunner(web_app)
    loop.run_until_complete(runner.setup())
    site = web.TCPSite(runner, port=8080)
    loop.run_until_complete(site.start())

    executor.start_polling(dp, skip_updates=True)
