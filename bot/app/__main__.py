#import logging
#import sys
#import os
#import asyncio
#from datetime import datetime, timezone
#from aiogram import Bot, Dispatcher
#from aiogram.fsm.storage.memory import MemoryStorage
#from handlers.setup import setup_message_handler
#from web_handlers.setup import setup_web_handler
#from db import DB
#
#async def run_bot(bot,dp) -> None:
#    await dp.start_polling(bot)
#
#if __name__ == "__main__":
#    admin_chat = os.environ['admin_chat']
#    tg_token = os.environ['tg_token']
#
#    db_name = os.environ['db_name']
#    db_user = os.environ['db_user']
#    db_pass = os.environ['db_pass']
#    db_host = os.environ['db_host']
#    db_port = os.environ['db_port']
#
#    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
#
#    storage = MemoryStorage()
#    bot = Bot(token=tg_token, parse_mode="HTML")
#    dp = Dispatcher()
#    db = DB(db_name,db_user,db_pass,db_host,db_port)
#
#    setup_message_handler('start')
#    setup_message_handler('build')
#    setup_message_handler('destroy')
#    setup_message_handler('support')
#    setup_message_handler('ban')
#    setup_message_handler('unban')
#
#    setup_web_handler('test')
#
#    asyncio.run(run_bot(bot,dp))


import logging
import sys
import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from handlers.setup import setup_message_handler
#from web_apps.setup import setup_web_app
from db import DB
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from aiohttp.web import run_app
from aiohttp.web_app import Application

def main():
    from web_apps.test import test_handler

#    setup_message_handler('start')
#    setup_message_handler('build')
#    setup_message_handler('destroy')
#    setup_message_handler('support')
    setup_message_handler('ban')
#    setup_message_handler('unban')

#    setup_web_handler('test')

    app = Application()
    app["bot"] = bot
    app.router.add_post("/demo/sendMessage", test_handler)
    SimpleRequestHandler(
        dispatcher=dispatcher,
        bot=bot,
    ).register(app,path = "/webhook")

    setup_application(app, dispatcher, bot=bot)

    run_app(app, host="127.0.0.1", port=8081)

if __name__ == "__main__":
    admin_chat = os.environ['admin_chat']
    tg_token = os.environ['tg_token']

    db_name = os.environ['db_name']
    db_user = os.environ['db_user']
    db_pass = os.environ['db_pass']
    db_host = os.environ['db_host']
    db_port = os.environ['db_port']

    storage = MemoryStorage()
    bot = Bot(token=tg_token, parse_mode="HTML")
    db = DB(db_name,db_user,db_pass,db_host,db_port)

    dispatcher = Dispatcher(bot)
    dispatcher.startup.register(on_startup)
    logging.basicConfig(level=logging.INFO)
    main()
