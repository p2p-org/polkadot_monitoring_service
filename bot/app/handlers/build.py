from functions import deploy
from __main__ import dp, db, bot, admin_chat
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup, ReplyKeyboardRemove
from datetime import datetime, timezone
  
@dp.message_handler(commands=["build"])
async def command_build(message: Message) -> None:
    if message.chat.type == 'group':
        await message.answer("🧑<200d>🤝<200d>🧑 Group chats are not allowed.\nSorry and have a good day.",reply_markup=ReplyKeyboardRemove())
        return

    username = message.chat.username
    chat_id = message.from_user.id
    account_status = db.get_records('account_status','id',chat_id)
    grafana_status = db.get_records('grafana_status','id',chat_id)

    if not grafana_status:
        await message.answer("You have no registered yet.\nPlease call /start.",reply_markup=ReplyKeyboardRemove())
        return

    elif grafana_status == 'on':
        await message.answer("According to our database you already have an instance 🤷\n\nFeel free to contact us /support if any questions.",reply_markup=ReplyKeyboardRemove())
        return
    elif account_status == 'off':
        await message.answer("Your account has been disabled 🤷\nSorry and have a good day.",reply_markup=ReplyKeyboardRemove())
        return

    deploy(chat_id,'./values.yml')

    db.update_record(chat_id,'grafana_status','on')
    db.update_record(chat_id,'grafana_deploy_time',datetime.now(timezone.utc))

    await bot.send_message(admin_chat, "Someone initialized of deploy grafana.\nUsername: @{username} ID: {chat_id}\n\nCommands:\n/delete {chat_id}\n/ban {chat_id}".format(username=username,chat_id=chat_id),reply_markup=ReplyKeyboardRemove())
    await bot.send_message(chat_id,"Alright 👍\n\nOur robots started cooking your personal dashboard. Usually, this process takes around 5 minutes.\nWe will send all necessary data as soon as dashboard will be ready!\n\nFeel free to contact us /support if any questions.",reply_markup=ReplyKeyboardRemove())
