from __main__ import dp, db, bot, admin_chat
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from callback_query_handlers import admin_buttons

class Form(StatesGroup):
    support = State()

@dp.message_handler(state=Form.support)
async def process_support(message: Message, state: FSMContext) -> None:
    username = message.chat.username
    chat_id = message.from_user.id

    menu = InlineKeyboardMarkup().add(InlineKeyboardButton(text="Answer", callback_data=admin_buttons.cb.new(action="support_open")),
               InlineKeyboardButton(text="Close", callback_data=admin_buttons.cb.new(action="support_close")),
               InlineKeyboardButton(text="Ban", callback_data=admin_buttons.cb.new(action="admin_ban")))

    if message.text:
        if '/' in message.text:
            await message.answer("Unexpected charaster in your message.",reply_markup=ReplyKeyboardRemove())
            await state.reset_state()
            return

        await bot.send_message(admin_chat, "Username: @{} ChatId: {}\nMessage:\n{}".format(username,chat_id,message.text),reply_markup=menu)
        await message.answer("Got it!!!\nYou will get an answer from our team soon.")
    elif message.photo:
        await bot.send_photo(admin_chat,message.photo[0].file_id)
        await bot.send_message(admin_chat, "Username: @{} ChatId: {} \nCaption: {}".format(username,chat_id,message.caption),reply_markup=menu)

    await state.reset_state()
    db.update_record(chat_id,'support_status','on')
    return
