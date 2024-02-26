from __main__ import bot, router, db, admin_chat, grafana_url
from aiogram import F
from aiogram.types import CallbackQuery, Message
from aiogram.exceptions import TelegramBadRequest
from callback_data.main import CbData
from utils.menu_builder import MenuBuilder

async def main_menu(message: Message):
    username = message.chat.username
    chat_id = message.from_user.id
    message_id = message.message_id

    account_status = db.get_records('account_status','id',chat_id)
    
    menu = MenuBuilder()
    menu.button(text="Open Grafana", url=grafana_url) + "size=1"
    menu.button(text="Manage Subscribtions", callback_data=CbData(dst="sub_menu", data="", id=0).pack()) + "size=1"
    menu.button(text="Help", callback_data=CbData(dst='support_menu', data="", id=0).pack()) + "size=1"
    menu.build()

    if not account_status:
        db.add_account(chat_id,username)
        
        await message.bot.send_message(admin_chat, text="Username: @" + username + " ID:" + chat_id + "\nHas just PRE-registered.")
        
    try:
        await message.edit_text("✋✋✋ Welcome to a validator monitoring bot by P2P.org\n\nWe tried to collect lots of metrics related to validators behavior in substrate based networks and expose it through Telegram bot.\n\nNote: We collect metrics for one month, you can get historical data through Grafana.",reply_markup=menu.as_markup())
    except TelegramBadRequest:
        await message.answer("✋✋✋ Welcome to a validator monitoring bot by P2P.org\n\nWe tried to collect lots of metrics related to validators behavior in substrate based networks and expose it through Telegram bot.\n\nNote: We collect metrics for one month, you can get historical data through Grafana.",reply_markup=menu.as_markup())

@router.callback_query(CbData.filter(F.dst == 'main_menu'))
async def main_menu_from_cb(query: CallbackQuery):
    await main_menu(query.message)
    await query.answer()
