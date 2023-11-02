from __main__ import db, bot, web, web_app, subs
from aiohttp.web_request import Request
from aiohttp.web_response import json_response
from aiogram.types import WebAppInfo
from aiogram.types import ReplyKeyboardRemove
import logging
from utils.subscriptions import Alert


async def handler(request: Request):
    a = await request.json()
    alert = Alert(a)

    if alert.severity and alert.alertname:
        ids = db.get_records('id','promalert_status','on')
        
        if isinstance(ids, int):
            ids = [{'id':ids}]
        for i in ids:
            if subs.must_notify(i['id'], alert):
                await bot.send_message(i['id'], '\n'.join([
                   f'Alert: {alert.alertname}', 
                   f'Severity: {alert.severity}',
                   f'Description: {alert.description}']))

    return web.json_response({'status':'ok'}) ## To be reviewed

def register_app():
    web_app.add_routes([web.post('/prom_alert', handler)])
