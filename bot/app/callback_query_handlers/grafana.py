from functions import deploy
from __main__ import dp, db, bot, admin_chat
from aiogram.types import CallbackQuery,InlineKeyboardButton,InlineKeyboardMarkup
from datetime import datetime, timezone

cb = CallbackData('row', 'func','action')

@dp.callback_query_handler(cb.filter(func='grafana_instances'))
async def menu_prom_cb_handler(query: CallbackQuery):
    await query.answer(query.id)
    chat_id = query['from']['id']
    message_id = query['message']['message_id']

    grafana_status = db.get_records('grafana_status','id',chat_id)

    if grafana_status == 'on':
        keyboard = InlineKeyboardMarkup().add(InlineKeyboardButton(text="Delete", callback_data=cb.new(func='operate_grafana',action='delete')),
                                              InlineKeyboardButton(text="Back", callback_data=cb.new(func='operate_grafana',action='back')))

        await bot.send_message(chat_id,"According to our database you already have an instance 🤷\n\n",reply_markup=keyboard)
        return
    
    #deploy(chat_id,'./values.yml')

    db.update_record(chat_id,'grafana_status','on')
    db.update_record(chat_id,'grafana_deploy_time',datetime.now(timezone.utc))

    await bot.send_message(admin_chat, "Someone initialized of deploy grafana.\nUsername: @{username} ID: {chat_id}".format(username=username,chat_id=chat_id))
    await bot.send_message(chat_id,"Alright 👍\n\nOur robots started cooking your personal dashboard. Usually, this process takes around 5 minutes.\nWe will send all necessary data as soon as dashboard will be ready!\n\nFeel free to contact us /support if any questions.",reply_markup=ReplyKeyboardRemove())
