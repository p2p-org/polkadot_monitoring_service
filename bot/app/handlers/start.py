from __main__ import dp, db, bot, admin_chat
from aiogram.types import Message

@dp.message_handler(commands=["start"])
async def command_start(message: Message) -> None:
    if message.chat.type == 'group':
        await message.answer("🧑<200d>🤝<200d>🧑 Group chats are not allowed.\nSorry and have a good day.")
        await state.reset_state()
        return

    username = message.chat.username
    chat_id = message.from_user.id
    status = db.get_record(chat_id,'status')

    if not status:
        await bot.send_message(admin_chat, "Username: @{} ID: {}\nHas just PRE-registered.".format(username,chat_id))
        await message.answer("Hi there 👋\n\n\nWelcome to a validator monitoring bot by P2P.org\n\n\n\nFeel free to contact us /support if any questions.")

        db.add_account(chat_id,username,'None','inactive','inactive')

    else:
        await message.answer("According to our database you already registered. 🤷\n\nFeel free to contact us /support if any questions.")

