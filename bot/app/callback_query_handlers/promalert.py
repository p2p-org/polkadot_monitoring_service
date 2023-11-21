from callback_data.main import CbData
from __main__ import router, db, subs
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import F
from utils.menu_builder import MenuBuilder
from utils.db import DB
from utils.subscriptions import Subscriptions
from aiogram.fsm.context import FSMContext

assert isinstance(db, DB)
assert isinstance(subs, Subscriptions)

def promalert_dialog(promalert_status: str = '', chat_id: int = 0) -> (str, InlineKeyboardBuilder):
    s = subs.get_subscriptions(chat_id)
    if promalert_status == '':
        promalert_status = db.get_records('promalert_status', 'id', chat_id)
    text = []
    if promalert_status != 'on':
        promalert_status = 'off'
    text.append(f'Notifications: {promalert_status}')
    text.append(f'Subscriptions count: {len(s)}')

    menu = MenuBuilder()
    if promalert_status == 'off':
        menu.add(preset='promalert_on')
    else:
        menu.add(preset='promalert_off')
    menu.add(preset='sub_rules')
    if len(s) > 0:
        menu.add(preset='sub_list')
    return '\n'.join(text), menu.build(button_back='main_menu')

@router.callback_query(CbData.filter(F.dst == 'promalert'))
async def handle_promalert(query: CallbackQuery):
    text, keyboard = promalert_dialog(chat_id=query.message.chat.id)
    call = query.message.edit_text(text=text, reply_markup=keyboard.as_markup())
    await query.bot(call)
    await query.answer('alerts menu')

@router.callback_query(CbData.filter(F.dst == 'promalert_on'))
async def handle_promalert_on(query: CallbackQuery):
    db.update_record(query.message.chat.id, 'promalert_status', 'on')
    text, keyboard = promalert_dialog(chat_id=query.message.chat.id, promalert_status='on')
    call = query.message.edit_text(text=text, reply_markup=keyboard.as_markup())
    await query.bot(call)
    await query.answer('notifications enabled')

@router.callback_query(CbData.filter(F.dst == 'promalert_off'))
async def handle_promalert_off(query: CallbackQuery):
    db.update_record(query.message.chat.id, 'promalert_status', 'off')
    text, keyboard = promalert_dialog(chat_id=query.message.chat.id, promalert_status='off')
    call = query.message.edit_text(text=text, reply_markup=keyboard.as_markup())
    await query.bot(call)
    await query.answer('notifications disabled')
