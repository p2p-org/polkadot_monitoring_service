from __main__ import dp, db, bot
from aiogram.utils.callback_data import CallbackData
from aiogram.types import CallbackQuery,InlineKeyboardButton,InlineKeyboardMarkup

cb = CallbackData('row', 'action')

@dp.callback_query_handler(cb.filter(action='promalert_menu'))
async def menu_prom_cb_handler(query: CallbackQuery):
    chat_id = query['from']['id']
    message_id = query['message']['message_id']

    keyboard = InlineKeyboardMarkup().add(InlineKeyboardButton(text="Set", callback_data=cb.new(action='promalert_set')),
                                          InlineKeyboardButton(text="Deactivate", callback_data=cb.new(action='promalert_deactivate')))
    
    await bot.send_message(chat_id,"You can subscribe or deactivate subsription hete.",reply_markup=keyboard)
    await query.answer(query.id)

@dp.callback_query_handler(cb.filter(action='promalert_set'))
async def menu_prom_cb_handler(query: CallbackQuery):
    chat_id = query['from']['id']
    message_id = query['message']['message_id']

    await bot.delete_message(chat_id,message_id)
    
    db.update_record(chat_id,'promalert_status','on')
    
    await bot.send_message(chat_id,"Alright!\n\nFrom now you able to receive predefined alerts.")
    
    await query.answer(query.id)

@dp.callback_query_handler(cb.filter(action='promalert_deactivate'))
async def menu_prom_cb_handler(query: CallbackQuery):
    chat_id = query['from']['id']
    message_id = query['message']['message_id']

    await bot.delete_message(chat_id,message_id)

    db.update_record(chat_id,'promalert_status','off')

    await bot.send_message(chat_id,"Your subscriprion has been deactivated.")
    await query.answer(query.id) 
