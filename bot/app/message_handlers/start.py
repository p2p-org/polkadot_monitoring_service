from __main__ import router
from aiogram.types import Message
from aiogram import F
from callback_query_handlers.main_menu import main_menu

@router.message(F.text == '/start')
async def command_start(message: Message) -> None:
    await main_menu(message,'from_message_handler')
