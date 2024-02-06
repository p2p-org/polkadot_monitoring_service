from __main__ import  bot, db, router
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters.state import State, StatesGroup
from aiogram.exceptions import TelegramBadRequest
from aiogram import F
from callback_data.main import CbData
from utils.menu_builder import MenuBuilder
from utils.alerts import Alerts
from forms.subscribtions import Form
import re

@router.callback_query(CbData.filter(F.dst == 'sub_menu'))
async def sub_menu(query: CallbackQuery):
    chat_id = query.message.chat.id
    message_id = query.message.message_id
    promalert_status = db.get_records('promalert_status', 'id', chat_id)
    
    text = "Here is a main subscriptions menu.\n\nSubscribe and track neccesary events in network.\n\n"

    menu = MenuBuilder()
      
    menu.button(text='📨 My Subscribtions', callback_data=CbData(dst="sub_manage", data="", id=0).pack()) + "size=1"
    menu.button(text="⚙️  My accounts", callback_data=CbData(dst="acc_menu", data="", id=0).pack()) + "size=1"
    menu.button(text="⬅️  Back", callback_data=CbData(dst="main_menu", data="", id=0).pack()) + "size=2"

    if promalert_status == 'off':
        menu.button(text='🔕 Unmute', callback_data=CbData(dst="promalert_on", data="", id=0).pack()) + "size=2"
    else:
        menu.button(text="🔔 Mute", callback_data=CbData(dst="promalert_off", data="", id=0).pack()) + "size=2"
    
    menu.build()

    try:
        await query.message.edit_text(text, reply_markup=menu.as_markup())
    except TelegramBadRequest:
        pass

    await query.answer()

@router.callback_query(CbData.filter(F.dst == 'promalert_on'))
async def handle_promalert_on(query: CallbackQuery):
    db.update_record(query.message.chat.id, 'promalert_status', 'on')
    
    await query.answer('Unmuted')
    await sub_menu(query)

@router.callback_query(CbData.filter(F.dst == 'promalert_off'))
async def handle_promalert_off(query: CallbackQuery):
    db.update_record(query.message.chat.id, 'promalert_status', 'off')
    
    await query.answer('Muted')
    await sub_menu(query)

@router.callback_query(CbData.filter(F.dst == 'sub_manage'))
async def sub_manage(query: CallbackQuery, state: FSMContext):
    chat_id = query.message.chat.id
    d = await state.get_data()
    
    await state.clear()
    
    alerts = Alerts(chat_id)
    templates = alerts.list_templates()
     
    menu = MenuBuilder()
    
    for template in templates:
        uniqueid = int(template['labels']['uniqueid'])
        r = alerts.get_rule(uniqueid=uniqueid)

        if len(r) == 0:
            menu.button(text="➕ " + template['alert'], callback_data=CbData(dst='sub_edit', data="", id=uniqueid)) + "size=1"
        else:
            menu.button(text="🟢 " + template['alert'], callback_data=CbData(dst='sub_view', data="", id=uniqueid)) + "size=1"

    menu.button(text="⬅️  Back", callback_data=CbData(dst="sub_menu", data="", id=0).pack()) + "size=2"
    menu.button(text="🧠 Learn", callback_data=CbData(dst="support_subscribtions", data="", id=0).pack()) + "size=2"
    menu.build()

    try:
        await query.message.edit_text(text="<b>Here you can choose all necessary subscbtions for you.\n\nFor now we cover:\nPolkadot/Kusama and some parachains like Moonbeam/Moonriver, Acala/karura, Astar/Shiden.\n\nYou can always contribute to alert expressions list by edit prometheus template in project(Button Learn)</b>", reply_markup=menu.as_markup())
    except TelegramBadRequest:
        pass

    await query.answer()

@router.callback_query(CbData.filter(F.dst == 'sub_view'))
async def sub_view(query: CallbackQuery):
    chat_id = query.message.chat.id
    uniqueid = int(query.data.split(':')[3])

    alerts = Alerts(chat_id)
    template = alerts.get_template(uniqueid)
    rule = alerts.get_rule(uniqueid)

    labels = ""
    
    for k,v in rule['labels'].items():
        if k == 'chat_id' or k == 'uniqueid':  
            continue
        
        if k == 'accounts':
            if len(v.split('|')) < 8:
                v = [addr[:3] + '..' + addr[-3:] for addr in v.replace('(','').replace(')','').split('|')]
                v = ', '.join(v)
            else:
                v = str(len(v.split('|'))) + ' accounts in rule'
        
        labels += k + ': ' + str(v) + '\n'
    
    text = '<b>🔹 ' + template['alert'] + '\n\n' + '🔻 ' + template['annotations']['bot_description'] + '\n\n' + 'Labels:\n' + labels + '</b>'

    menu = MenuBuilder()

    menu.button(text="❌ Delete", callback_data=CbData(dst="sub_delete", data="", id=uniqueid).pack()) + "size=1"
    menu.button(text="⬅️  Back", callback_data=CbData(dst="sub_manage", data="", id=0).pack()) + "size=1"

    menu.build()

    try:
        await query.message.edit_text(text, reply_markup=menu.as_markup())
    except TelegramBadRequest:
        pass

    await query.answer()

@router.callback_query(CbData.filter(F.dst == 'sub_edit'))
async def sub_edit(query: CallbackQuery, state: FSMContext):
    chat_id = query.message.chat.id
    uniqueid = int(query.data.split(':')[3])
    
    d = await state.get_data()

    alerts = Alerts(chat_id)
    template = alerts.get_template(uniqueid)

    mandatory_filters = alerts.get_variables(template=template)
   
    if isinstance(d, dict) and len(d.keys()) == 0:
        await state.set_state(Form.subscribtions)

        check_list = {'id': uniqueid, 'check_list':{i:{'data': 'undefined', 'emoji': '❌ '} for i in mandatory_filters if i != 'chat_id'}}
    elif isinstance(d,dict) and len(d.keys()) > 0:
        check_list = d
    else:
        check_list = {} 

    if 'accounts' in check_list['check_list'].keys():
        try:
            validators = db.get_records('validators', 'id', chat_id).split(' ')
        except AttributeError:
            await query.answer('Please define accounts. Subsbtions menu -> My accounts')
            validators = 'undefined'
        
        if len(validators) > 0 and validators != 'undefined':
            check_list['check_list']['accounts']['data'] = validators
            check_list['check_list']['accounts']['emoji'] = '✅ '
    
    await state.set_data(check_list)

    check_list_text = ""

    for k,v in check_list['check_list'].items():
        if k == 'accounts' and v['data'] != 'undefined':
            check_list_text += v['emoji'] + k.capitalize() + ': ' + str(len(v['data'])) + ' accounts in portfolio.'
        else:
            check_list_text += v['emoji'] + k.capitalize() + ': ' + v['data']

        check_list_text += "\n"
        
    text = '<b>🔹 ' + template['alert'] + '\n\n' + '🔻' + template['annotations']['bot_description'] + "\n\n<b>Mandatory filters:</b>\n" + check_list_text + "\n\n</b>"

    menu = MenuBuilder()

    if 'interval' in check_list['check_list'].keys():
        menu.button(text='Set time interval',callback_data=CbData(dst="sub_set_interval", data="", id=uniqueid).pack()) + "size=1"
    
    if 'threshold' in check_list['check_list'].keys():
        menu.button(text="Select threshold", callback_data=CbData(dst="sub_set_threshold", data="reset", id=uniqueid).pack()) + "size=1"

    if 'chain' in check_list['check_list'].keys():
        menu.button(text='Set chain', callback_data=CbData(dst="sub_set_chain", data="", id=uniqueid).pack()) + "size=1"
    
    if isinstance(d,dict) and len(d.keys()) > 0:
        statuses = [v['data'] for k,v in d['check_list'].items()]

        if 'undefined' not in statuses:
            await query.answer('We are ready to Go!!! Click Back to activate.')
            menu.button(text="⬅️  Back", callback_data=CbData(dst="sub_save", data="", id=0).pack()) + "size=2"
        else:
            menu.button(text="⬅️  Back", callback_data=CbData(dst="sub_manage", data="", id=0).pack()) + "size=2"

    else:
        menu.button(text="⬅️  Back", callback_data=CbData(dst="sub_manage", data="", id=0).pack()) + "size=2"
        
    menu.button(text="❌ Clear", callback_data=CbData(dst="clear_state", data="", id=uniqueid).pack()) + "size=2"

    menu.build()

    try:
        await query.message.edit_text(text, reply_markup=menu.as_markup())
    except TelegramBadRequest:
        pass
    
    await query.answer()

@router.callback_query(CbData.filter(F.dst == 'sub_set_interval'))
async def sub_set_interval(query: CallbackQuery, state: FSMContext):
    uniqueid = int(query.data.split(':')[3])
    interval = query.data.split(':')[2]
    
    d = await state.get_data()
    intervals = ['30s','1m','2m','5m','10m','30m']
        
    if interval:
        d['check_list']['interval']['data'] = interval
        d['check_list']['interval']['emoji'] = '✅ '
        
        await state.set_data(d)
        await sub_edit(query,state)
    else:
        menu = MenuBuilder()
    
        for interval in intervals:
            menu.button(text=interval, callback_data=CbData(dst="sub_set_interval", data=interval, id=uniqueid).pack()) + "size=3"
        
        menu.button(text="Back", callback_data=CbData(dst="sub_edit", data="", id=uniqueid).pack()) + "size=1"
        menu.build()
     
        await state.set_data(d)
        await query.message.edit_text(text="Please select time interval.\n\n", reply_markup=menu.as_markup())

@router.callback_query(CbData.filter(F.dst == 'sub_set_chain'))
async def sub_set_interval(query: CallbackQuery, state: FSMContext):
    uniqueid = int(query.data.split(':')[3])
    chain = query.data.split(':')[2]

    d = await state.get_data()
    chains = ['polkadot','kusama']

    if chain:
        d['check_list']['chain']['data'] = query.data.split(':')[2]
        d['check_list']['chain']['emoji'] = '✅ '

        await state.set_data(d)
        await sub_edit(query,state)

    else:
        menu = MenuBuilder()

        for chain in chains:
            menu.button(text=chain, callback_data=CbData(dst="sub_set_chain", data=chain, id=uniqueid).pack()) + "size=1"

        menu.button(text="Back", callback_data=CbData(dst="sub_edit", data="", id=uniqueid).pack()) + "size=1"
        menu.build()

        await state.set_data(d)
        await query.message.edit_text(text="Please select the chain.\n\nCurrently only Polkadot and Kusama possible.\n\n", reply_markup=menu.as_markup())

@router.callback_query(CbData.filter(F.dst == 'sub_set_threshold'))
async def sub_set_threshold(query: CallbackQuery, state: FSMContext):
    uniqueid = int(query.data.split(':')[3])
    data = query.data.split(':')[2]
    
    d = await state.get_data()
   
    threshold_min = 0 
    threshold_max = 100000
    
    try:
        digit = str(query.data.split(':')[2])
        if digit == "reset":
            d['check_list']['threshold']['data'] = ""
            d['check_list']['threshold']['emoji'] = '❌ '
        else:
            d['check_list']['threshold']['data'] += digit
            d['check_list']['threshold']['emoji'] = '✅ '
    
    except TypeError:
        d['check_list']['threshold']['data'] = ""
        d['check_list']['threshold']['emoji'] = '❌ '

    await state.set_data(d)

    message_id = query.message.message_id
    chat_id = query.message.chat.id

    menu = MenuBuilder()
    menu.button(text="1", callback_data=CbData(dst="sub_set_threshold", data="1", id=uniqueid).pack()) + "size=3"
    menu.button(text="2", callback_data=CbData(dst="sub_set_threshold", data="2", id=uniqueid).pack()) + "size=3"
    menu.button(text="3", callback_data=CbData(dst="sub_set_threshold", data="3", id=uniqueid).pack()) + "size=3"
    menu.button(text="4", callback_data=CbData(dst="sub_set_threshold", data="4", id=uniqueid).pack()) + "size=3"
    menu.button(text="5", callback_data=CbData(dst="sub_set_threshold", data="5", id=uniqueid).pack()) + "size=3"
    menu.button(text="6", callback_data=CbData(dst="sub_set_threshold", data="6", id=uniqueid).pack()) + "size=3"
    menu.button(text="7", callback_data=CbData(dst="sub_set_threshold", data="7", id=uniqueid).pack()) + "size=3"
    menu.button(text="8", callback_data=CbData(dst="sub_set_threshold", data="8", id=uniqueid).pack()) + "size=3"
    menu.button(text="9", callback_data=CbData(dst="sub_set_threshold", data="9", id=uniqueid).pack()) + "size=3"
    menu.button(text="Save", callback_data=CbData(dst="sub_edit", data="", id=uniqueid).pack()) + "size=3"
    menu.button(text="0", callback_data=CbData(dst="sub_set_threshold", data="0", id=uniqueid).pack()) + "size=3"
    menu.button(text="Reset", callback_data=CbData(dst="sub_set_threshold", data="reset", id=uniqueid).pack()) + "size=3"
    menu.build()

    try:
        await query.message.edit_text(text="Set threshold value. Limit: 100000\n\n" + "Value: " + d['check_list']['threshold']['data'], reply_markup=menu.as_markup())
    except TelegramBadRequest:
        pass

    await query.answer()

@router.callback_query(CbData.filter(F.dst == 'clear_state'))
async def clear_state(query: CallbackQuery, state: FSMContext):
    await state.clear()
    await sub_edit(query=query,state=state)

@router.callback_query(CbData.filter(F.dst == 'sub_save'))
async def sub_save(query: CallbackQuery, state: FSMContext):
    chat_id = query.message.chat.id
    d = await state.get_data()
    
    uniqueid = d['id']
    check_list = d['check_list']

    alerts = Alerts(chat_id)
    template = alerts.get_template(uniqueid)

    alerts.add_rule(uniqueid=uniqueid, check_list=check_list, template=template)
    
    await query.answer('Subscribtion has been added')
    await sub_manage(query,state)

@router.callback_query(CbData.filter(F.dst == 'sub_delete'))
async def sub_delete(query: CallbackQuery, state: FSMContext):
    chat_id = query.message.chat.id
    uniqueid = int(query.data.split(':')[3])

    alerts = Alerts(chat_id)

    alerts.delete_rule(uniqueid=uniqueid)
    
    await query.answer('Subscribtion has been deleted')
    await sub_manage(query,state)
