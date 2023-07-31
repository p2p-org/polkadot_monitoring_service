from __main__ import dp, db, bot, admin_chat
from aiogram.types import Message

@dp.message_handler(commands=["unban"])
async def command_unban(message: Message) -> None:
    if str(message.chat.id) == admin_chat:
        try:
            chat_id = message.text.split(" ")[1]
        except IndexError:
            await message.reply("Expected an userId as argument.")
            return

        status = db.get_record(chat_id,'status')

        if status == 'banned':
            await message.reply("Unbanned.")
            await bot.send_message(chat_id, "Your account has unbanned by our team.\nFeel free to contact us /support if any questions.")
            db.update_record(chat_id,'status','inactive')
        else:
            await message.reply("Wrong status: " + str(status))

