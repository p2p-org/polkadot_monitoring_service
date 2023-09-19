from __main__ import dp, db, bot
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from callback_query_handlers import admin_buttons

class Form(StatesGroup):
    admin_send_msg = State()

@dp.message_handler(state=Form.admin_send_msg)
async def process_support(message: Message, state: FSMContext) -> None:
    username = message.chat.username
    chat_id = message.from_user.id

    if '/' in message.text:
        await message.answer("Unexpected charaster in your message.",reply_markup=ReplyKeyboardRemove())
        await state.reset_state()
        return

    menu = InlineKeyboardMarkup().add(InlineKeyboardButton(text="Continue", callback_data=admin_buttons.cb.new(action="support_open")),
               InlineKeyboardButton(text="Close", callback_data=admin_buttons.cb.new(action="support_close")))


    await bot.send_message(chat_id, "Message:\n{}".format(message.text),reply_markup=menu)

    await state.reset_state()
    db.update_record(chat_id,'support_status','off')
    return
