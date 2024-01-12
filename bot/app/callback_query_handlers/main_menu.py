from __main__ import bot, router, db, admin_chat, grafana_url
from aiogram import F
from aiogram.types import CallbackQuery, Message
from callback_data.main import CbData
from utils.menu_builder import MenuBuilder

async def main_menu(message: Message, from_message_handler: str = None):
    username = message.chat.username
    chat_id = message.from_user.id
    message_id = message.message_id

    account_status = db.get_records('account_status','id',chat_id)
    
    menu = MenuBuilder()
    menu.button(text="Open Grafana", url=grafana_url) + "size=1"
    menu.button(text="Manage Prometheus alerts", callback_data=CbData(dst="sub_menu",data="").pack()) + "size=1"
    menu.button(text="Contact us(support)", callback_data=CbData(dst='support',data="").pack()) + "size=1"
    menu.build()

   # if not account_status:
   #     keyboard = MenuBuilder()
   #     keyboard.add()
   #     await message.bot.send_message(admin_chat, text="Username: @{} ID: {}\nHas just PRE-registered.".format(username,chat_id), reply_markup=keyboard.build().as_markup())
   #     db.add_account(chat_id,username)
        
    if from_message_handler:
        await message.answer("Welcome to a validator monitoring bot by P2P.org\n\n\n\n",reply_markup=menu.as_markup())
    else:
        await message.edit_text("Welcome to a validator monitoring bot by P2P.org\n\n\n\n",reply_markup=menu.as_markup())

@router.callback_query(CbData.filter(F.dst == 'main_menu'))
async def main_menu_from_cb(query: CallbackQuery):
    await main_menu(query.message)
    await query.answer()
