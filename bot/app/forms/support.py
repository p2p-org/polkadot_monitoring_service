from __main__ import router, db, admin_chat
from utils.db import DB
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.filters.state import State, StatesGroup
from utils.menu_builder import MenuBuilder

assert isinstance(db, DB)
class Form(StatesGroup):
    support = State()
    admin_send_msg = State()

@router.message(Form.support)
async def handle_client_input(message: Message, state: FSMContext) -> None:
    await state.clear()
    keyboard = MenuBuilder()
    keyboard.add(preset='support_reply_start',data=str(message.from_user.id))
    keyboard.add(preset='support_off',data=str(message.from_user.id))
    keyboard.add(preset='toggle_ban',data=str(message.from_user.id))
    username = message.chat.username
    if message.text:
        await message.bot.send_message(admin_chat, f'Username: @{username}\nMessage:\n{message.text}\n',
            reply_markup=keyboard.build().as_markup())
    elif message.photo:
        await message.bot.send_photo(admin_chat,message.photo[0].file_id)
        await message.bot.send_message(admin_chat, f'Username: @{username} + \nCaption:\n{message.caption}\n',
            reply_markup=keyboard.build().as_markup())

    await message.answer('Please wait for the answer')

@router.message(Form.admin_send_msg)
async def handle_admin_input(message: Message, state: FSMContext) -> None:
    keyboard = MenuBuilder()
    keyboard.add(preset='support_reply_submit', data=str(message.from_user.id))
    keyboard.add(preset='support_reply_cancel', data=str(message.from_user.id))
    chat_id = message.from_user.id
    try:
        d = await state.get_data()
    except:
        message.answer("Could not read client chat_id")
        return

    d['response'] = message.text
    await state.set_data(d)
    await message.bot.send_message(chat_id, f'Are you sure you want to send following message to {d["client_chat_id"]}?:\n{message.text}',
        reply_markup=keyboard.build().as_markup())
