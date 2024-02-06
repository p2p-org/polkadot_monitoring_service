from __main__ import router,bot
from aiogram.types import Message
from aiogram import F
from forms.accounts import Form 
from callback_query_handlers.main_menu import main_menu

@router.message(F.text == '/start')
async def command_start(message: Message) -> None:
    chat_id = message.from_user.id
    message_id = message.message_id
    
    await main_menu(message)
    await bot.delete_message(chat_id,message_id)

@router.message(F.text)
async def command_start(message: Message) -> None:
    chat_id = message.from_user.id
    message_id = message.message_id
    
    if Form.validators:
        await bot.delete_message(chat_id,message_id)
