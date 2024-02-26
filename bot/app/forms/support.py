from __main__ import bot, router, cache, admin_chat
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.filters.state import State, StatesGroup
from callback_data.main import CbData
from utils.menu_builder import MenuBuilder

class Form(StatesGroup):
    support = State()

@router.message(Form.support)
async def find_account(message: Message, state: FSMContext):
    chat_id = message.from_user.id
    message_id = message.message_id
    username = message.chat.username

    msg = message.text

    old_menu = await state.get_data()

    keyboard = MenuBuilder()
    keyboard.button(text="⬅️  Back to menu", callback_data=CbData(dst='support_menu', data="", id=0).pack()) + "size=1"
    keyboard.build()

    text = "Your message been sent to our team.\nWe will contact you if it necessary."

    await message.answer(text, reply_markup=menu.as_markup())
    await state.clear()
    await bot.send_message(admin_chat, text="User @" + username + " sends message:\n" + str(msg))
    await bot.delete_message(old_menu['chat_id'], old_menu['message_id'])
    await bot.delete_message(chat_id, message_id)
