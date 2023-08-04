from functions import destroy
from __main__ import dp, db, bot, admin_chat
from aiogram.types import Message

@dp.message_handler(commands=["destroy"])
async def command_destroy(message: Message) -> None:
    if str(message.chat.id) == admin_chat:
        initializator = 'admin'

        try:
            chat_id = message.text.split(" ")[1]
        except IndexError:
            await message.reply("Expected userId after delemiter.")
            return
    else:
        initializator = 'user'
        chat_id = message.from_user.id

    grafana_status = db.get_records('grafana_status','id',chat_id)

    if initializator == 'admin' and grafana_status == 'on':
        await message.answer("Destroy initialized.")
        await bot.send_message(chat_id, "Your instance has been destroy by admin.\n\nFeel free to contact us /support if any questions.")
        db.update_record(chat_id,'grafana_status','off')
        functions.deploy(chat_id,'destroy')
    elif initializator == 'user' and grafana_status == 'on':
        username = db.get_records('username','id',chat_id)
        await message.answer("Destroy initialized. It will take couple of minutes.\n\nFeel free to contact us /support if any questions.")
        await bot.send_message(admin_chat, "Username: @{} ID: {}\nHas destroyed his grafana.".format(username,chat_id))
        db.update_record(chat_id,'grafana_status','off')
        destroy(chat_id,'./values.yml')
    else:
        await message.reply("Wrong status: " + str(status))
