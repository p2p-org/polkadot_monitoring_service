from __main__ import dp, db, bot, admin_chat
from aiohttp.web_request import Request
from aiohttp.web_response import json_response
from aiogram.types import WebAppInfo

async def test(request: Request):
    data = await request.post()
    
    if data["id"]:
        chat_id = data['id']
        
        await bot.send_message(chat_id, "Your account has been banned 🤷\nSorry and have a good day.")
    else:
        return json_response({"ok": False})

    return json_response({"ok": True})
