from __main__ import db, dp, bot
from aiogram import BaseMiddleware
from aiogram.types import Message,CallbackQuery
from aiogram.dispatcher.event.bases import CancelHandler
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional,Awaitable
from aiogram.types.update import Update
import asyncio

@dp.update.outer_middleware()
async def check_if_blocked(handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],event: Update,data: Dict[str, Any]) -> Any:
    if event.event_type == 'message':
        chat_id = event.message.chat.id
        message_id = event.message.message_id
    elif event.event_type == 'callback_query':
        chat_id = event.callback_query.from_user.id
        message_id = event.callback_query.message.message_id 

    if str(chat_id).startswith('-'):
        await event.message.answer("🧑🤝🧑 Group chats are not allowed.\nSorry and have a good day.")
        return

    account_status = db.get_records('account_status','id',chat_id)
   
    #if isinstance(account_status, list):
    #    await bot.delete_message(chat_id, message_id)
    #    CancelHandler()

    if account_status == 'off':
        if event.event_type == 'message':
            await event.message.answer("Your account has been disabled.")
            CancelHandler()
        elif event.event_type == 'callback_query':
            await event.callback_query.answer('Your account has been disabled.')
            CancelHandler()
    else:
        return await handler(event, data)
