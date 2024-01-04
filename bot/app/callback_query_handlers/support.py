from __main__ import router, db, bot
from callback_data.main import CbData
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from callback_query_handlers.main_menu import main_menu
from forms.support import Form
from aiogram import F
from utils.menu_builder import MenuBuilder


### User actions
@router.callback_query(CbData.filter(F.dst == 'support'))
async def handle_support_menu(query: CallbackQuery):
    chat_id = query.message.chat.id
    message_id = query.message.message_id
    keyboard = MenuBuilder()
    # don't even show support button to banned users
    if db.get_records('account_status','id',chat_id) == 'on':
        keyboard.add(preset='support_request')

    await bot.send_message(chat_id,'Useful things like wiki or chat will be later.\n\n',reply_markup=keyboard.build(button_back='main_menu').as_markup())
    await bot.delete_message(chat_id,message_id)
    await query.answer('help menu')

@router.callback_query(CbData.filter(F.dst == 'support_request'))
async def handle_support_request(query: CallbackQuery, state: FSMContext):
    chat_id = query.message.chat.id
    support_status = db.get_records('support_status','id',chat_id)
    if support_status == 'on':
        await bot.send_message(chat_id,'Please wait until we answer')
        await state.clear()
        await query.answer('Ok')
        return

    keyboard = MenuBuilder()
    await state.set_state(Form.support)
    call = query.message.answer(text=
        'Enter your question or describe the issue in one message.\n'+
        'Press <b>Back</b> if you changed your mind', reply_markup=keyboard.build(button_back='support_cancel').as_markup())

    await query.bot(call)
    db.update_record(chat_id,'support_status','on')
    await query.answer('Ok')

@router.callback_query(CbData.filter(F.dst == 'support_cancel'))
async def handle_support_cancel(query: CallbackQuery, state: FSMContext):
    await state.clear()
    text, keyboard = main_menu()
    call = query.message.edit_text(text=text, reply_markup=keyboard.as_markup())
    await query.bot(call)
    await query.answer('Got it. Hope you are okay')

### Admin actions
@router.callback_query(CbData.filter(F.dst == 'support_reply_cancel'))
async def handle_support_reply_cancel(query: CallbackQuery, callback_data: CbData, state: FSMContext):
    #db.update_record(int(callback_data.data), 'support_status', 'off')
    await state.clear()
    call = query.message.delete()
    await query.answer('Response canceled')
    await query.bot(call)

@router.callback_query(CbData.filter(F.dst == 'support_reply_start'))
async def handle_support_reply_start(query: CallbackQuery, callback_data: CbData, state: FSMContext):
    try:
        client_chat_id = int(callback_data.data)
    except:
        await query.answer('Something went wrong. chat_id not found.')
        return

    keyboard = MenuBuilder()
    keyboard.add(preset='support_reply_cancel', data=str(client_chat_id))
    call = query.message.reply(text=f'@{query.from_user.username} initiated conversation with {callback_data.data}. Please enter response text',
        reply_markup=keyboard.build().as_markup())
    
    await state.set_state(Form.admin_send_msg)
    await state.set_data({'client_chat_id': client_chat_id})
    await query.bot(call)
    await query.answer('Ok')

@router.callback_query(CbData.filter(F.dst == 'support_reply_submit'))
async def handle_support_reply_submit(query: CallbackQuery, state: FSMContext):
    d = await state.get_data()
    try:
        d['client_chat_id']
        d['response']
    except KeyError:
        await query.answer('Outdated')
        await query.bot.delete_message(chat_id=query.from_user.id, message_id=query.message.message_id)
        return
    await query.bot.send_message(chat_id=d['client_chat_id'], text=f'P2P support team:\n{d["response"]}')
    db.update_record(d['client_chat_id'], 'support_status', 'off')
    await state.clear()
    await query.answer('Sent')

@router.callback_query(CbData.filter(F.dst == 'support_off'))
async def handle_support_off(query: CallbackQuery, callback_data: CbData):
    db.update_record(int(callback_data.data), 'support_status', 'off')
    await query.answer('Ok')

@router.callback_query(CbData.filter(F.dst == 'toggle_ban'))
async def handle_toggle_ban(query: CallbackQuery, callback_data: CbData):
    chat_id = int(callback_data.data)
    
    if db.get_records('account_status', 'id', chat_id) == 'off':
        db.update_record(chat_id, 'account_status', 'on')
        await bot.send_message(chat_id, 'Your account has been activated🎉\n')
        await query.answer('Unbanned')
    else:
        db.update_record(chat_id, 'account_status', 'off')
        db.update_record(chat_id, 'support_status', 'off')
        await bot.send_message(chat_id, 'Your account has been deactivated by our team 🤷\n')
        await query.answer('Banned')
    
