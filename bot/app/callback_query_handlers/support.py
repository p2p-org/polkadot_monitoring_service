from __main__ import router,db,bot,cb
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State,StatesGroup
from forms.support import Form
from aiogram import F
from utils.menu_builder import MenuBuilder

@router.callback_query(cb.filter(F.dst == 'support'))
async def menu_prom_cb_handler(query: CallbackQuery,callback_data: cb):
    await query.answer(query.id)

    username = query.message.chat.username
    chat_id = query.message.chat.id
    message_id = query.message.message_id

    menu = MenuBuilder()
    keyboard = menu.build(callback_data=cb,button_back='main_menu')

    await bot.send_message(chat_id,"Useful things like wiki or chat will be later.\n\n",reply_markup=keyboard.as_markup())
    await bot.delete_message(chat_id,message_id)

@router.callback_query(cb.filter(F.dst == 'support_on'))
async def menu_support_cb_handler(query: CallbackQuery, state: FSMContext):
    await query.answer(query.id)

    username = query.message.chat.username
    chat_id = query.message.chat.id
    message_id = query.message.message_id

    support_status = db.get_records('support_status','id',chat_id)
   
    if support_status == 'on':
        await bot.send_message(chat_id,"Please wait until we answer")
        await state.reset_state()
        return
    
    await state.set_state(Form.support)
    await bot.send_message(chat_id, "Please enter your message.")
