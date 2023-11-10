from __main__ import router,db,bot,cb,admin_chat
from aiogram.types import Message 
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State,StatesGroup
from forms.support import Form
from aiogram import F
from utils.menu_builder import MenuBuilder

@router.message(state=Form.support)
async def process_support(message: Message) -> None:
    username = message.chat.username
    chat_id = message.from_user.id
    
    menu = MenuBuilder()
    user_keyboard = menu.build(callback_data=cb,preset='support_text',button_back='support',button_main_meny=True)
    admin_keyboard = menu.build(callback_data=cb,preset='support_reply')

    if message.text:
        await bot.send_message(admin_chat, "Username: @{}\nMessage:\n{}\n\n".format(username,message.text),reply_markup=admin_keyboard.as_markup())
    elif message.photo:
        await bot.send_photo(admin_chat,message.photo[0].file_id)
        await bot.send_message(admin_chat, "Username: @{} + \nCaption: {}\n\n".format(username,message.caption),reply_markup=admin_keyboard.as_markup())

    await message.answer("Got it!!!\nYou will get an answer from our team soon.\n\n",reply_markup=user_keyboard.as_markup())

    await state.reset_state()
    
    db.update_record(chat_id,'support_status','on')
