from __main__ import db, bot, web, web_app
from aiohttp.web_request import Request
from aiohttp.web_response import json_response
from callback_data.main import CbData
from utils.menu_builder import MenuBuilder
import logging
import yaml


async def handler(request: Request):
    a = await request.json()
    print(yaml.dump(a))

    if isinstance(a, dict) and 'alerts' in a.keys(): 
        chat_id = int(a['commonLabels']['chat_id'])
        promalert_status = db.get_records('promalert_status', 'id', chat_id)

        if promalert_status == 'on':
            if a['status'] == 'firing':
                text = "🆘 <b>THE ROOF IS ON FIRE</b> 🔥🔥🔥\n\n" + a['commonAnnotations']['summary'] + "\n\n🔻 " + a['commonAnnotations']['description']

            elif a['status'] == 'resolved':
                text = "✅ RESOLVED 🌞🌞🌞\n\n" + a['commonAnnotations']['summary'] + "\n\n🔹 " + a['commonAnnotations']['description'] 
            else:
                text = "❔ UNKNOWN STATUS\n\n" + a['commonAnnotations']['summary'] + "\n\n🔹 " + a['commonAnnotations']['description']
    
            keyboard = MenuBuilder()
            keyboard.button(text="Hide", callback_data=CbData(dst="delete_message", data="", id=0).pack()) + "size=1"
            keyboard.build()

            
            await bot.send_message(chat_id, text, reply_markup=keyboard.as_markup())

            return web.Response(status=200)
        else:
            return web.Response(status=401)
    else:
        return web.Response(status=500) 
    
def register_app():
    web_app.add_routes([web.post('/prom_alert', handler)])
