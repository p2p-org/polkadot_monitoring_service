from __main__ import router,dp,db,bot,cb
from aiogram.types import CallbackQuery,InlineKeyboardButton,InlineKeyboardMarkup
from utils.menu_builder import MenuBuilder
from aiogram import F

@router.callback_query(cb.filter(F.dst == 'main_menu'))
async def menu_prom_cb_handler(query: CallbackQuery,callback_data: cb):
    chat_id = query.message.chat.id
    message_id = query.message.message_id

    menu = MenuBuilder()
    menu = menu.build(callback_data=cb,preset='main_menu')
  
    await bot.send_message(chat_id,"Here is a main menu.",reply_markup=menu.as_markup())
    await bot.delete_message(chat_id,message_id)
    await query.answer(query.id)

