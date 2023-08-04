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

        account_status = db.get_records('account_status','id',chat_id)

        if account_status == 'off':
            db.update_record(chat_id,'account_status','on')
            await message.reply("Unbanned.")
            await bot.send_message(chat_id, "Your account has enabled by our team.\nFeel free to contact us /support if any questions.")
        else:
            await message.reply("Wrong status: " + str(account_status))

