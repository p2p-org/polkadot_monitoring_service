from __main__ import  bot, router
from aiogram.types import CallbackQuery
from aiogram.exceptions import TelegramBadRequest
from aiogram import F
from callback_data.main import CbData

@router.callback_query(CbData.filter(F.dst == 'delete_message'))
async def delete_message(query: CallbackQuery):
    chat_id = query.message.chat.id
    message_id = query.message.message_id
    
    await bot.delete_message(chat_id, message_id)
