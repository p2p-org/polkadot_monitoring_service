import logging
import sys
import os
import asyncio
from datetime import datetime, timezone
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor
from handlers.setup import setup_message_handler
#from webserver.setup import setup_webserver_handler
from db import DB

if __name__ == "__main__":
    admin_chat = os.environ['admin_chat']
    tg_token = os.environ['tg_token']

    db_name = os.environ['db_name']
    db_user = os.environ['db_user']
    db_pass = os.environ['db_pass']
    db_host = os.environ['db_host']
    db_port = os.environ['db_port']

    logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    storage = MemoryStorage()
    bot = Bot(token=tg_token, parse_mode="HTML")
    dp = Dispatcher(bot, storage=storage)

    db = DB(db_name,db_user,db_pass,db_host,db_port)

    setup_message_handler('start')
    setup_message_handler('build')
    setup_message_handler('destroy')
    setup_message_handler('support')
    setup_message_handler('ban')
    setup_message_handler('unban')

#    setup_webserver_handler('test')

    executor.start_polling(dp, skip_updates=True)
