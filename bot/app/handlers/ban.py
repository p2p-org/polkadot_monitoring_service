from __main__ import dp, db, bot, admin_chat
from aiogram.types import Message

@dp.message_handler(commands=["ban"])
async def command_ban(message: Message) -> None:
    if str(message.chat.id) == admin_chat:
        try:
            chat_id = message.text.split(" ")[1]
        except IndexError:
            await message.reply("Expected an userId as argument.")
            return

        account_status = db.get_records('account_status','id',chat_id)

        if account_status != 'off':
            await message.reply("Banned.\n\nCommands:\n/unban {}".format(chat_id))

            await bot.send_message(chat_id, "Your account has been disabled 🤷\nSorry and have a good day.")
            db.update_record(chat_id,'account_status','off')
            db.update_record(chat_id,'support_status','off')
        else:
            await message.reply("Wrong status: " + str(status))
