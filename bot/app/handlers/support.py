from __main__ import dp, db, bot, admin_chat
from fsm.support import Form
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.dispatcher import FSMContext

@dp.message_handler(commands=["support"])
async def command_support(message: Message, state: FSMContext) -> None:
    if str(message.chat.id).startswith('-'):
        await message.answer("Group chats are not allowed.\nSorry and have a good day.",reply_markup=ReplyKeyboardRemove())
        await state.reset_state()
        return

    username = message.chat.username
    chat_id = message.from_user.id
    status = db.get_record(chat_id,'status')
    support_status = db.get_record(chat_id,'support_status')

    if not status:
        await message.answer("You have no registered yet.\nPlease call /start.",reply_markup=ReplyKeyboardRemove())
        await state.reset_state()
        return

    if support_status == 'active':
        await message.answer("You already have an active support conversation.\nPlease wait until admin close it.",reply_markup=ReplyKeyboardRemove())
        await state.reset_state()
        return

    if status == 'banned':
        await message.answer("Your account has been banned 🤷\nSorry and have a good day.",reply_markup=ReplyKeyboardRemove())
        await state.reset_state()
        return

    await state.set_state(Form.support)
    await message.answer("Please enter your message.",reply_markup=ReplyKeyboardRemove())
    await bot.send_message(admin_chat, "Username: @{} ID: {}\nHas just opened support chat conversation.".format(username,chat_id),reply_markup=ReplyKeyboardRemove())

@dp.message_handler(state=Form.support)
async def process_support(message: Message, state: FSMContext) -> None:
    username = message.chat.username
    chat_id = message.from_user.id

    if message.text:
        if '/' in message.text:
            await message.answer("Unexpected charaster in your message.",reply_markup=ReplyKeyboardRemove())
            await state.reset_state()
            return

        await bot.send_message(admin_chat, "Username: @{}\nMessage:\n{}\n\nCommands:\n/support_reply {} Your answer.\n/deactivate_support {}\n/ban {}".format(username,message.text,chat_id,chat_id,chat_id),reply_markup=ReplyKeyboardRemove())
        await message.answer("Got it!!!\nYou will get an answer from our team soon.\n\nTo build your grafana use /build",reply_markup=ReplyKeyboardRemove())
    elif message.photo:
        await bot.send_photo(admin_chat,message.photo[0].file_id)
        await bot.send_message(admin_chat, "Username: @{} + \nCaption: {}\n\nCommands:\n/support_reply {} Your answer.\n/deactivate_support {}\n/ban {}".format(username,message.caption,chat_id,chat_id,chat_id),reply_markup=ReplyKeyboardRemove())

    await state.reset_state()
    db.update_record(chat_id,'support_status','active')
    return

@dp.message_handler(commands=["support_reply"])
async def command_support_reply(message: Message) -> None:
    username = message.chat.username
    chat_id = message.from_user.id

    if str(message.chat.id) == admin_chat:
        try:
            a = ' '.join(message.text.split(" ")[2:])
            answer = a + "\n"
        except IndexError:
            answer = None

        chat_id = message.text.split(" ")[1]

        await message.reply("Replied.\n\nCommands:\n/deactivate_support {chat_id}\n/ban {chat_id}".format(chat_id=chat_id),reply_markup=ReplyKeyboardRemove())
        await bot.send_message(chat_id, "Message from P2P team:\n{}".format(answer),reply_markup=ReplyKeyboardRemove())

@dp.message_handler(commands=["deactivate_support"])
async def command_deactivate_support(message: Message) -> None:
    if str(message.chat.id) == admin_chat:
        try:
            chat_id = message.text.split(" ")[1]
        except IndexError:
            await message.reply("Expected an userId as argument.",reply_markup=ReplyKeyboardRemove())
            return

    await message.reply("Deactivated.",reply_markup=ReplyKeyboardRemove())
    db.update_record(chat_id,'support_status','inactive')
