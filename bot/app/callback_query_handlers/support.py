from __main__ import dp, db, bot, admin_chat
from aiogram.utils.callback_data import CallbackData
from aiogram.types import CallbackQuery,InlineKeyboardButton,InlineKeyboardMarkup
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from forms.support import Form

cb = CallbackData('row', 'action')

@dp.callback_query_handler(cb.filter(action='support'))
async def menu_support_cb_handler(query: CallbackQuery, state: FSMContext):
    chat_id = query['from']['id']
    username = query['from']['username']
    message_id = query['message']['message_id']
    
    support_status = db.get_records('support_status','id',chat_id)
   
    if support_status == 'on':
        await bot.send_message(chat_id,"Please wait until we answer")
        await state.reset_state()
        return
    
    await state.set_state(Form.support)
    await bot.send_message(chat_id, "Please enter your message.")

    await query.answer(query.id)
