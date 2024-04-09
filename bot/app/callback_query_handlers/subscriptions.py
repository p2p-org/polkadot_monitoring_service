from __main__ import  bot, db, router
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters.state import State, StatesGroup
from aiogram.exceptions import TelegramBadRequest
from aiogram import F
from callback_data.main import CbData
from utils.menu_builder import MenuBuilder
from utils.alerts import Alerts
from forms.subscriptions import Form
import re

@router.callback_query(CbData.filter(F.dst == 'sub_menu'))
async def sub_menu(query: CallbackQuery):
    chat_id = query.message.chat.id
    message_id = query.message.message_id
    promalert_status = db.get_records('promalert_status', 'id', chat_id)
    
    text = "Subscribe and receive alerts to same chat from bot.\n\n☝️ What is possible for now:\n🔸[Polakdot/Kusama] session/staking data like era points, slashes, active validators and other common network metrics\n🔸[Polakdot/Kusama] PV events like backing of candidates and disputes\n🔸[Polakdot/Kusama] consensus participation(GRANDPA).\n🔸[Acala/Karura] session/staking data like era points, slashes, active validators and other common network metrics.\n🔸[Moonbeam/Moonriver] session/staking data like era points, slashes, active validators and other common network metrics.\n\n☝️ Checkout docs https://github.com/p2p-org/polkadot_monitoring_service/tree/main/docs to learn how we collect metrics and know list of all of them."
    
    menu = MenuBuilder()
      
    menu.button(text='📨 My Subscriptions', callback_data=CbData(dst="sub_manage", data="", id=0).pack()) + "size=1"
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
        
        rule_from_file = alerts.get_rule_from_file(uniqueid=uniqueid)
        rule_from_prom = alerts.get_rule_from_prom(uniqueid=uniqueid)
        
        if len(rule_from_file) == 0:
            menu.button(text="➕ " + template['alert'], callback_data=CbData(dst='sub_edit', data="", id=uniqueid)) + "size=1"
        else:
            if len(rule_from_prom) == 0:
                menu.button(text="⏳ " + template['alert'], callback_data=CbData(dst='sub_view', data="", id=uniqueid)) + "size=1"
            else:
                if rule_from_prom['state'] == 'firing':
                    menu.button(text="🔥🔥🔥 " + template['alert'], callback_data=CbData(dst='sub_view', data="", id=uniqueid)) + "size=1"
                elif rule_from_prom['state'] == 'pending':
                    menu.button(text="🔥 " + template['alert'], callback_data=CbData(dst='sub_view', data="", id=uniqueid)) + "size=1"
                elif rule_from_prom['state'] == 'inactive':
                    menu.button(text="🟢 " + template['alert'], callback_data=CbData(dst='sub_view', data="", id=uniqueid)) + "size=1"
                else:
                    menu.button(text="⁉️  " + template['alert'], callback_data=CbData(dst='sub_view', data="", id=uniqueid)) + "size=1"


    menu.button(text="⬅️  Back", callback_data=CbData(dst="sub_menu", data="", id=0).pack()) + "size=1"
    menu.build()

    try:
        await query.message.edit_text(text="Here you can subscribe to all the necessary events on the network and more.\n\n☝️ Every subscription represents prometheus alert rule - possbile to customize it easily.\nFollow github docs https://github.com/p2p-org/polkadot_monitoring_service/tree/main/docs to learn how it works inside of the box(no code interventions needed).\n\nEmoji explanations:\n➕ - Set alert\n⏳ - Waiting for activation\n🟢 - Alert is ready\n⁉️  - Alert added but activation failed by some reasons(Contact US)\n🔥 - Alert expecting\n🔥🔥🔥 - FIRE!!! You will receive an alert soon", reply_markup=menu.as_markup())
    except TelegramBadRequest:
        pass

    await query.answer()

@router.callback_query(CbData.filter(F.dst == 'sub_view'))
async def sub_view(query: CallbackQuery):
    chat_id = query.message.chat.id
    uniqueid = int(query.data.split(':')[3])

    alerts = Alerts(chat_id)
    template = alerts.get_template(uniqueid)

    rule = alerts.get_rule_from_prom(uniqueid)

    labels = ""
    state = "Deployment"
    
    if 'labels' in rule.keys():
        for k,v in rule['labels'].items():
            if k == 'chat_id' or k == 'uniqueid' or k == 'labels_source':  
                continue
            
            if k == 'accounts':
                if len(v.split('|')) < 8:
                    v = [addr[:3] + '..' + addr[-3:] for addr in v.replace('(','').replace(')','').split('|')]
                    v = ', '.join(v)
                else:
                    v = str(len(v.split('|'))) + ' accounts in rule'
            
            labels += k + ': ' + str(v) + '\n'

        state = rule['state']
    
    text = '🔹 ' + template['alert'] + '\n\n' + '🔻 ' + template['annotations']['bot_description'] + '\n' + 'Labels:\n' + labels + '\n\n' + 'State: <b>' + state + '</b>' 

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
        await state.set_state(Form.subscriptions)

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

    check_list_text = "      "

    for k,v in check_list['check_list'].items():
        if k == 'accounts' and v['data'] != 'undefined':
            check_list_text += v['emoji'] + k.capitalize() + ': ' + str(len(v['data'])) + ' accounts in portfolio.'
        else:
            check_list_text += v['emoji'] + k.capitalize() + ': ' + str(v['data'])

        check_list_text += "\n      "
        
    text = '🔹 ' + template['alert'] + '\n\n' + '🔻 ' + template['annotations']['bot_description'] + "\n\n🔸 Mandatory filters:\n" + check_list_text + "\n\n"

    menu = MenuBuilder()

    if 'project' in check_list['check_list'].keys():
        menu.button(text='Select projects',callback_data=CbData(dst="sub_set_labels", data=".project", id=uniqueid).pack()) + "size=1"

    if 'chain' in check_list['check_list'].keys():
        menu.button(text='Select chains', callback_data=CbData(dst="sub_set_labels", data=".chain", id=uniqueid).pack()) + "size=1"

    if 'interval' in check_list['check_list'].keys():
        menu.button(text='Set time interval',callback_data=CbData(dst="sub_set_interval", data="", id=uniqueid).pack()) + "size=1"
    
    if 'threshold' in check_list['check_list'].keys():
        menu.button(text="Set threshold", callback_data=CbData(dst="sub_set_threshold", data="reset", id=uniqueid).pack()) + "size=1"

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


@router.callback_query(CbData.filter(F.dst == 'sub_set_labels'))
async def sub_set_labels(query: CallbackQuery, state: FSMContext):
    chat_id = query.message.chat.id
    uniqueid = int(query.data.split(':')[3])

    d = await state.get_data()
    
    if query.data.split(':')[2].startswith('.'):
        label_name = query.data.split(':')[2].replace('.', '').split(',')[0]
        
        try:
            label_value = query.data.split(':')[2].replace('.', '').split(',')[1]
        except IndexError:
            label_value = None

    try:
        if label_value and label_value == "reset":
            d['check_list'][label_name]['data'] = ""
            d['check_list'][label_name]['emoji'] = '❌ '

        else:
            try:
                if label_value:
                    if label_value.startswith('-'):
                        d['check_list'][label_name]['data'].remove(label_value[1:])
                    else:
                        d['check_list'][label_name]['data'].append(label_value)
            except AttributeError:
                d['check_list'][label_name]['data'] = [label_value]
                d['check_list'][label_name]['emoji'] = '✅ '

    except (TypeError, AttributeError):
        d['check_list'][label_name]['data'] = ""
        d['check_list'][label_name]['emoji'] = '❌ '

    alerts = Alerts(chat_id)
    template = alerts.get_template(uniqueid)
    
    label_values = alerts.get_labels(template, label_name)
    
    menu = MenuBuilder()

    if isinstance(label_values, list) and len(label_values) > 0:
        for label in label_values:
            if label in d['check_list'][label_name]['data']:
                menu.button(text='🟢 ' + label, callback_data=CbData(dst="sub_set_labels", data="."+label_name + ',-' + label, id=uniqueid).pack()) + "size=1"
            else:
                menu.button(text=label, callback_data=CbData(dst="sub_set_labels", data="."+label_name + ',' + label, id=uniqueid).pack()) + "size=1"
    
    menu.button(text="⬅️  Back", callback_data=CbData(dst="sub_edit", data="", id=uniqueid).pack()) + "size=2"
    menu.button(text="Reset", callback_data=CbData(dst="sub_set_labels", data="."+label_name + ',' + "reset", id=uniqueid).pack()) + "size=2"
    menu.build()

    await state.set_data(d)
    await query.message.edit_text(text="Please select labels from list bellow.\n\n", reply_markup=menu.as_markup())


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
        
        menu.button(text="⬅️   Back", callback_data=CbData(dst="sub_edit", data="", id=uniqueid).pack()) + "size=1"
        menu.build()
     
        await state.set_data(d)
        await query.message.edit_text(text="Please select time interval.\n\n", reply_markup=menu.as_markup())


@router.callback_query(CbData.filter(F.dst == 'sub_set_threshold'))
async def sub_set_threshold(query: CallbackQuery, state: FSMContext):
    uniqueid = int(query.data.split(':')[3])
    data = query.data.split(':')[2]
    
    d = await state.get_data()
   
    try:
        digit = str(query.data.split(':')[2])
        
        if digit == "reset":
            d['check_list']['threshold']['data'] = ""
            d['check_list']['threshold']['emoji'] = '❌ '
        
        else:
            if len(d['check_list']['threshold']['data']) < 5:
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
    
    if len(d['check_list']['threshold']['data']) > 0:
        menu.button(text="Save", callback_data=CbData(dst="sub_edit", data="", id=uniqueid).pack()) + "size=3"
    else:
        menu.button(text="Back", callback_data=CbData(dst="sub_edit", data="", id=uniqueid).pack()) + "size=3"
    
    menu.button(text="0", callback_data=CbData(dst="sub_set_threshold", data="0", id=uniqueid).pack()) + "size=3"
    menu.button(text="Reset", callback_data=CbData(dst="sub_set_threshold", data="reset", id=uniqueid).pack()) + "size=3"
    menu.build()

    try:
        await query.message.edit_text(text="Here you can type necessary threshold value.\n\nValue: " + d['check_list']['threshold']['data'], reply_markup=menu.as_markup())
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
    
    await query.answer('Subscription has been added')
    await sub_manage(query,state)

@router.callback_query(CbData.filter(F.dst == 'sub_delete'))
async def sub_delete(query: CallbackQuery, state: FSMContext):
    chat_id = query.message.chat.id
    uniqueid = int(query.data.split(':')[3])

    alerts = Alerts(chat_id)

    alerts.delete_rule(uniqueid=uniqueid)
    
    await query.answer('Subscription has been deleted')
    await sub_manage(query,state)
