from __main__ import db, bot, web, web_app
from aiohttp.web_request import Request
from aiohttp.web_response import json_response
import logging


async def handler(request: Request):
    a = await request.json()

    print(a)
    
    return web.json_response({'status':'ok'}) ## To be reviewed

def register_app():
    web_app.add_routes([web.post('/prom_alert', handler)])
