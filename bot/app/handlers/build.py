from functions import deploy
from __main__ import dp, db, bot, admin_chat
from aiogram.types import Message
from aiogram.filters import Command
from datetime import datetime, timezone

  
@dp.message(Command(commands=["build"]))
async def command_build(message: Message) -> None:
    if message.chat.type == 'group':
        await message.answer("🧑<200d>🤝<200d>🧑 Group chats are not allowed.\nSorry and have a good day.")
        return

    username = message.chat.username
    chat_id = message.from_user.id
    status = db.get_record(chat_id,'status')
    instance_count_5m = int(db.get_count())

    if not status:
        await message.answer("You have no registered yet.\nPlease call /start.")
        return

    if instance_count_5m >= 3:
        await message.answer("❗ A lot of deployments at this moment.\nPlease wait for couple of minutes.\n\nFeel free to contact us /support to solve it.")
        await bot.send_message(admin_chat, "❗❗❗ A lot of deployments last 5 minutes❗❗❗")
        return

    elif status == 'active':
        await message.answer("According to our database you already have an instance 🤷\n\nFeel free to contact us /support if any questions.")
        return
    elif status == 'banned':
        await message.answer("Your account has been banned 🤷\nSorry and have a good day.")
        return

    deploy(chat_id,'./values.yml')

    db.update_record(chat_id,'status','active')
    db.update_record(chat_id,'deploy_time',datetime.now(timezone.utc))

    await bot.send_message(admin_chat, "Someone initialized of deploy grafana.\nUsername: @{username} ID: {chat_id}\n\nCommands:\n/delete {chat_id}\n/ban {chat_id}".format(username=username,chat_id=chat_id),reply_markup=ReplyKeyboardRemove())
    await bot.send_message(chat_id,"Alright 👍\n\nOur robots started cooking your personal dashboard. Usually, this process takes around 5 minutes.\nWe will send all necessary data as soon as dashboard will be ready!\n\nFeel free to contact us /support if any questions.")
