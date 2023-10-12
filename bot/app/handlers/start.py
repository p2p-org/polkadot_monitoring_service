from __main__ import dp, db, bot, admin_chat
from aiogram.types import Message

@dp.message_handler(commands=["start"])
async def command_start(message: Message) -> None:
    if str(message.chat.id).startswith('-'):
        await message.answer("🧑🤝🧑 Group chats are not allowed.\nSorry and have a good day.")
        await state.reset_state()
        return

    username = message.chat.username
    chat_id = message.from_user.id
    account_status = db.get_records('account_status','id',chat_id)

    if not account_status:
        db.add_account(chat_id,username)
        await bot.send_message(admin_chat, "Username: @{} ID: {}\nHas just PRE-registered.".format(username,chat_id))
        await message.answer("Hi there 👋\n\n\nWelcome to a validator monitoring bot by P2P.org. Following commands available:\n\n/build - create grafana\n/destroy - delete grafana if exists\n/promalert - activate/deactivate alert notifications\n/support - if you have questions")


    else:
        await message.answer("According to our database you already registered. 🤷\n\nFeel free to contact us /support if any questions.")

