from __main__ import router,dp,db,bot,cb
from aiogram.types import CallbackQuery,InlineKeyboardButton,InlineKeyboardMarkup
from aiogram import F
from utils.menu_builder import MenuBuilder


@router.callback_query(cb.filter(F.dst == 'promalert'))
async def menu_prom_cb_handler(query: CallbackQuery,callback_data: cb):
    await query.answer(query.id)
    
    username = query.message.chat.username
    chat_id = query.message.chat.id
    message_id = query.message.message_id

    menu = MenuBuilder()
    menu = menu.build(callback_data=cb,preset='promalert',button_back='main_menu')

    await bot.send_message(chat_id,"You can subscribe or deactivate subsription hete.",reply_markup=menu.as_markup())
    await bot.delete_message(chat_id,message_id)
