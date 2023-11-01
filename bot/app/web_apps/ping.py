from __main__ import bot, web, web_app
from aiohttp.web_request import Request
from aiohttp.web_response import json_response
from aiogram.types import WebAppInfo

async def handler_post(request: Request):
    data = await request.json()

    try:
        chat_id = data['chat_id']
    except KeyError:
        chat_id = None
    
    if chat_id:
        await bot.send_message(chat_id,'Pong')
        return web.Response(text="Pong, don't forget to check your messanger.")
    else:
        return web.Response(text="Pong. !!!Could not obtain chat_id from payload!!!.")

async def handler_get(request: Request):
    return web.Response(text="Pong")

def register_app():
    print(1)
    web_app.add_routes([web.post('/ping', handler_post)])
    web_app.add_routes([web.get('/ping', handler_get)])
