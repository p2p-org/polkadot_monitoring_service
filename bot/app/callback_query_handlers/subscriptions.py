from __main__ import  bot, db, router
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram import F
from callback_data.main import CbData
from utils.subscriptions import Subscriptions
from utils.menu_builder import MenuBuilder
from utils.msg_text import dict2text, text2dict
from forms.sub_filter import Form, sub_filter_input_validate

@router.callback_query(CbData.filter(F.dst == 'sub_menu'))
async def sub_menu(query: CallbackQuery):
    chat_id = query.message.chat.id
    message_id = query.message.message_id
    promalert_status = db.get_records('promalert_status', 'id', chat_id)
    
    menu = MenuBuilder()
    menu.button(text='Add subscriptions', callback_data=CbData(dst="sub_add",data="").pack()) + "size=1"
    menu.button(text='My subscriptions', callback_data=CbData(dst="sub_list",data="").pack()) + "size=1"
    
    if promalert_status == 'off':
        menu.button(text='Unmute',callback_data=CbData(dst="promalert_on",data="").pack()) + "size=2"
    else:
        menu.button(text='Mute',callback_data=CbData(dst="promalert_off",data="").pack()) + "size=2"

    menu.build(button_back='main_menu')
    
    await query.message.edit_text("Here is a main subscriptions menu.\n\nSubscribe and track neccesary events in network.\n\n", reply_markup=menu.as_markup())
    await query.answer()

@router.callback_query(CbData.filter(F.dst == 'promalert_on'))
async def handle_promalert_on(query: CallbackQuery):
    db.update_record(query.message.chat.id, 'promalert_status', 'on')
    
    await sub_menu(query)

@router.callback_query(CbData.filter(F.dst == 'promalert_off'))
async def handle_promalert_off(query: CallbackQuery):
    db.update_record(query.message.chat.id, 'promalert_status', 'off')

    await sub_menu(query)


#
## Show rules list after Add subscription click
#@router.callback_query(CbData.filter(F.dst == 'sub_rules'))
#async def handle_sub_rules(query: CallbackQuery, callback_data: CbData):
#    r = await subs.get_rules()
#    rules = r.list()
#    keyboard = MenuBuilder().add(preset='rules_list', data=rules, navigation=callback_data.data)
#    call = query.message.edit_text(text='Please select alert you would like to subscribe to.',
#        reply_markup=keyboard.build().as_markup())
#    await query.bot(call)
#    await query.answer('Ok')
#
## Show single rule for subscription and edit buttons
#@router.callback_query(CbData.filter(F.dst == 'sub_rule'))
#async def handle_sub_rule(query: CallbackQuery, callback_data: CbData):
#    r = await subs.get_rule_by_name(callback_data.data)
#    rule = r.dict()
#    keyboard = MenuBuilder()
#    keyboard.add(preset='sub_filter_edit', data=rule)
#    keyboard.add(preset='sub_save', data=r.alertname)
#    text = 'Use buttons to configure subscription "Edit ..." to specify filters, Save to subscribe or Back to cancel\n'
#    call = query.message.edit_text(text=text+dict2text(rule), reply_markup=keyboard.build(button_back='promalert').as_markup())
#    await query.bot(call)
#    await query.answer('Ok')
#
## Show existing subscriptions
#@router.callback_query(CbData.filter(F.dst == 'sub_list'))
#async def handle_sub_list(query: CallbackQuery, callback_data: CbData):
#    if callback_data.data == '':
#        new_page = 0
#    else:
#        new_page = int(callback_data.data.split('/')[0])
#    s, total = subs.get_subscription_by_index(query.from_user.id, new_page)
#    
#    keyboard = MenuBuilder()
#    keyboard.add(preset='sub_filter_edit', data=s.keys())
#    keyboard.add(preset='sub_del', data=s['alertname'][0])
#    keyboard.add(preset='sub_scroll', navigation=f'{new_page}/{total}')
#    call = query.message.edit_text(text=dict2text(s), reply_markup=keyboard.build().as_markup())
#    await query.bot(call)
#    await query.answer('Ok')
#
## Turn on form.sub_filter and wait for field value
#@router.callback_query(CbData.filter(F.dst == 'sub_edit'))
#async def handle_sub_edit(query: CallbackQuery, callback_data: CbData, state: FSMContext):
#    d = text2dict(query.message.text)
#    await state.set_data({'expect': callback_data.data, 'current': d, 'message_id': query.message.message_id})
#    await state.set_state(Form.sub_filter)
#    text = f'Please send list of values for field <b>{callback_data.data}</b>\n'
#    keyboard = MenuBuilder()
#    call = query.message.edit_text(text=text, reply_markup=keyboard.build(button_back='sub_edit_cancel').as_markup())
#    await query.bot(call)
#    await query.answer(f'Please send values for: {callback_data.data}')
#
## Cancel form.sub_filter go promalert
#@router.callback_query(CbData.filter(F.dst == 'sub_edit_cancel'))
#async def handle_sub_edit(query: CallbackQuery, state: FSMContext):
#    await state.clear()
#    text, keyboard = promalert_dialog(chat_id=query.from_user.id)
#    call = query.message.edit_text(text=text, reply_markup=keyboard.as_markup())
#    await query.bot(call)
#    await query.answer('Canceled')
#
## Save alert from text message to database
#@router.callback_query(CbData.filter(F.dst == 'sub_save'))
#async def handle_sub_save(query: CallbackQuery, callback_data: CbData, state: FSMContext):
#    await state.clear()
#    if callback_data.data == '':
#        await query.answer('Something went wrong. Please try later.')
#    sub = text2dict(query.message.text)
#    for key, val in sub.items():
#        valid, reason = sub_filter_input_validate(expected=key, got=val)
#        if not valid:
#            keyboard = MenuBuilder()
#            keyboard.add(preset='sub_filter_edit', data=sub)
#            keyboard.add(preset='sub_save', data=sub['alertname'][0])
#            text = f'Unable to subscribe: <b>{reason}</b>. Please edit {key} field.\n' 
#            await query.bot.send_message(text=text+dict2text(sub), chat_id=query.from_user.id,
#                reply_markup=keyboard.build(button_back='promalert').as_markup())
#            await query.answer(f'Please update {key}')
#            return
#    n = subs.user_subscribe(chat_id=query.from_user.id, subscription_name=callback_data.data, lvs=sub)
#    if n == 0:
#        await query.answer('Something went wrong. Please try later.')
#    text, keyboard = promalert_dialog(chat_id=query.from_user.id)
#    call = query.message.edit_text(text=text, reply_markup=keyboard.as_markup())
#    await query.bot(call)
#    await query.answer('Saved')
#
## Delete subscription
#@router.callback_query(CbData.filter(F.dst == 'sub_del'))
#async def handle_sub_del(query: CallbackQuery, callback_data: CbData, state: FSMContext):
#    await state.clear()
#    if callback_data.data == '':
#        await query.answer('Something went wrong. Please try later.')
#    subs.user_unsubscribe(chat_id=query.from_user.id, subscription_name=callback_data.data)
#    text, keyboard = promalert_dialog(chat_id=query.from_user.id)
#    call = query.message.edit_text(text=text, reply_markup=keyboard.as_markup())
#    await query.bot(call)
#    await query.answer('Deleted')
