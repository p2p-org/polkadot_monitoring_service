from __main__ import dp, db, bot
from aiogram.utils.callback_data import CallbackData
from aiogram.types import CallbackQuery,InlineKeyboardButton,InlineKeyboardMarkup

cb = CallbackData('row', 'action')

@dp.callback_query_handler(cb.filter(action='support_open'))
async def menu_prom_cb_handler(query: CallbackQuery):
    chat_id = query['from']['id']
    message_id = query['message']['message_id']

@dp.callback_query_handler(cb.filter(action='support_close'))
async def menu_prom_cb_handler(query: CallbackQuery):
    chat_id = query['from']['id']
    message_id = query['message']['message_id']


@dp.callback_query_handler(cb.filter(action='ban'))
async def menu_prom_cb_handler(query: CallbackQuery):
    chat_id = query['from']['id']
    message_id = query['message']['message_id']
