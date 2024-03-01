from __main__ import router, db, bot, admin_chat
from callback_data.main import CbData
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from forms.support import Form
from aiogram import F
from utils.menu_builder import MenuBuilder


@router.callback_query(CbData.filter(F.dst == 'support_menu'))
async def support_menu(query: CallbackQuery):
    chat_id = query.message.chat.id
    message_id = query.message.message_id
    
    text = "Here you can send some message to our team like bug report, questions, proposals etc."
    menu = MenuBuilder()

    menu.button(text='📨 Write us', callback_data=CbData(dst="support_send_message", data="", id=0).pack()) + "size=1"
    menu.button(text="⬅️  Back", callback_data=CbData(dst="main_menu", data="", id=0).pack()) + "size=1"

    menu.build()

    try:
        await query.message.edit_text(text, reply_markup=menu.as_markup())
    except TelegramBadRequest:
        pass

    await query.answer()

@router.callback_query(CbData.filter(F.dst == 'support_send_message'))
async def support_send_message(query: CallbackQuery, state: FSMContext):
    d = await state.get_data()

    message_id = query.message.message_id
    chat_id = query.message.chat.id

    menu = MenuBuilder()
    menu.button(text="Back", callback_data=CbData(dst="support_menu", data="", id=0).pack()) + "size=1"
    menu.build()

    await state.set_state(Form.support)
    await state.set_data({'chat_id':chat_id, 'message_id':message_id})
    await query.message.edit_text('Please enter the message for us.\nIt may contents some questions, reports etc.', reply_markup=menu.as_markup())
