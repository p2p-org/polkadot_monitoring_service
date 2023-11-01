from functions import deploy
from __main__ import dp, db, bot, admin_chat
from aiogram.types import CallbackQuery,InlineKeyboardButton,InlineKeyboardMarkup
from aiogram import F
from utils.menu_builder import MenuBuilder
from utils.functions import deploy,destroy
from datetime import datetime, timezone

@router.callback_query(cb.filter(F.dst == 'grafana'))
async def menu_prom_cb_handler(query: CallbackQuery,callback_data: cb):
    await query.answer(query.id)

    chat_id = query.message.chat.id
    message_id = query.message.message_id

    menu_builder = MenuBuilder()

    grafana_status = db.get_records('grafana_status','id',chat_id)

    if grafana_status == 'on':
        keyboard = menu_builder.build(callback_data=cb,preset='grafana_off',button_back='main_menu')
        await bot.send_message(chat_id,"According to our database you already have an instance 🤷\n\n",reply_markup=keyboard.as_markup())
    else:
        keyboard = menu_builder.build(callback_data=cb,preset='grafana_on',button_back='main_menu')
        await bot.send_message(chat_id,"Here you can setup your own grafana instance.\n\n",reply_markup=keyboard.as_markup())

    await bot.delete_message(chat_id,message_id)

@router.callback_query(cb.filter(F.dst == 'grafana_on'))
async def menu_prom_cb_handler(query: CallbackQuery,callback_data: cb):
    await query.answer(query.id)

    username = query.message.chat.username
    chat_id = query.message.chat.id
    message_id = query.message.message_id
    
    deploy(chat_id,'./values.yml')

    db.update_record(chat_id,'grafana_status','on')
    db.update_record(chat_id,'grafana_deploy_time',datetime.now(timezone.utc))


    menu_builder = MenuBuilder()
    keyboard = menu_builder.build(callback_data=cb,button_back='grafana',button_main_menu=True)

    await bot.send_message(admin_chat, "Someone initialized of deploy grafana.\nUsername: @{username} ID: {chat_id}".format(username=username,chat_id=chat_id))
    await bot.send_message(chat_id,"Alright 👍\n\nOur robots started cooking your personal dashboard. Usually, this process takes around 5 minutes.\nWe will send all necessary data as soon as dashboard will be ready!\n\n",reply_markup=keyboard.as_markup())

    await bot.delete_message(chat_id,message_id)

@router.callback_query(cb.filter(F.dst == 'grafana_off'))
async def menu_prom_cb_handler(query: CallbackQuery,callback_data: cb):
    await query.answer(query.id)
    
    username = query.message.chat.username
    chat_id = query.message.chat.id
    message_id = query.message.message_id

    destroy(chat_id,'./values.yml')

    db.update_record(chat_id,'grafana_status','off')
    #db.update_record(chat_id,'grafana_deploy_time',datetime.now(timezone.utc))

    menu_builder = MenuBuilder()
    keyboard = menu_builder.build(callback_data=cb,button_back='grafana',button_main_menu=True)

    await bot.send_message(admin_chat, "Someone initialized of destroy grafana.\nUsername: @{username} ID: {chat_id}".format(username=username,chat_id=chat_id))
    await bot.send_message(chat_id,"Alright 👍\n\nWe revoked your grafana instance",reply_markup=keyboard.as_markup())

    await bot.delete_message(chat_id,message_id)
