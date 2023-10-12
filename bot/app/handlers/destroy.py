from functions import destroy
from __main__ import dp, db, bot, admin_chat
from aiogram.types import Message

@dp.message_handler(commands=["destroy"])
async def command_destroy(message: Message) -> None:
    initializator = 'user'
    chat_id = message.from_user.id

    if str(message.chat.id) == admin_chat:
        initializator = 'admin'

        try:
            chat_id = message.text.split(" ")[1]
        except IndexError:
            await message.reply("Expected userId after delemiter.")
            return

    grafana_status = db.get_records('grafana_status','id',chat_id)

    if grafana_status != 'on':
        await message.reply("Nothing to destroy. Grafana status: " + str(grafana_status))
        return

    db.update_record(chat_id,'grafana_status','off')
    destroy(chat_id,'./values.yml')

    if initializator == 'admin' and grafana_status == 'on':
        await message.answer("Destroy initialized.")
        await bot.send_message(chat_id, "Your instance has been destroyed by admin.\n\nFeel free to contact us /support if any questions.")
    elif initializator == 'user' and grafana_status == 'on':
        username = db.get_records('username','id',chat_id)
        await message.answer("Instance will be destoryed in couple of minutes. Thank you for using our bot.\n\nFeel free to contact us /support if any questions.")
        await bot.send_message(admin_chat, "Username: @{} ID: {}\nHas destroyed his grafana.".format(username,chat_id))
