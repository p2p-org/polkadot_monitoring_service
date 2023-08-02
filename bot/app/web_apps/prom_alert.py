from __main__ import db, bot, web, web_app
from aiohttp.web_request import Request
from aiohttp.web_response import json_response
from aiogram.types import WebAppInfo
from aiogram.types import ReplyKeyboardRemove


async def handler(request: Request):
    alert = await request.json()

    try:
        severity = alert['alerts'][0]['labels']['severity']
    except (IndexError,KeyError):
        severity = None

    try:
        alertname = alert['alerts'][0]['labels']['alertname']
    except (IndexError,KeyError):
        alertname = None

    try:
        message = alert['alerts'][0]['annotations']['description']
    except (IndexError,KeyError):
        message = None

    if severity and alertname:
        ids = db.get_records('id','promalert_status','on')
        
        if isinstance(ids, int):
            ids = [{'id':ids}]
        
        for i in ids:
            await bot.send_message(i['id'], "Prometheus alerting\n\nSeverity: {}\nAlert name: {}\nMessage: {}\n\nYou can always disable notification such this by calling /promalert\n\nFeel free to contact us /support if any questions.".format(severity,alertname,message),reply_markup=ReplyKeyboardRemove())

    return web.json_response({'status':'ok'}) ## To be reviewed

def register_app():
    web_app.add_routes([web.post('/prom_alert', handler)])
