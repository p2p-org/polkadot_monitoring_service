from __main__ import bot, router, cache
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.filters.state import State, StatesGroup
from callback_data.main import CbData
from utils.menu_builder import MenuBuilder

class Form(StatesGroup):
    validators = State()

@router.message(Form.validators)
async def find_account(message: Message, state: FSMContext):
    chat_id = message.from_user.id
    message_id = message.message_id
    
    old_menu = await state.get_data()
    msg = message.text

    menu = MenuBuilder()

    if msg.isalnum() and (len(msg) >= 3 and len(msg) <= 55):
        c = cache.get(msg)

        if len(c) > 0:
            for addr in c:
                human_addr = addr[:6] + '...' + addr[-6:]
                
                menu.button(text=human_addr, callback_data=CbData(dst='acc_save', data=addr[:20], id=0).pack()) + "size=1"
            
            menu.button(text="Back", callback_data=CbData(dst='acc_menu', data="", id=0).pack()) + "size=1"
            menu.build()
            
            await state.clear()
            await message.answer('We could find ' + str(len(c)) + ' accounts.\n\nSelect one of them or click Back.\n\n', reply_markup=menu.as_markup())
            await bot.delete_message(old_menu['chat_id'], old_menu['message_id'])
        
    await bot.delete_message(chat_id, message_id)
