from __main__ import router,dp,db,admin_chat
from utils.menu_builder import MenuBuilder
from aiogram.types import Message
from aiogram import F

@router.message(F.text == '/start')
async def command_start(message: Message) -> None:
    username = message.chat.username
    chat_id = message.from_user.id
    account_status = db.get_records('account_status','id',chat_id)
    
    menu = MenuBuilder()
    menu = menu.build(preset='main_menu')

    if not account_status:
        keyboard = MenuBuilder()
        keyboard.add(preset='toggle_ban',data=str(message.from_user.id))
        await message.bot.send_message(admin_chat, text="Username: @{} ID: {}\nHas just PRE-registered.".format(username,chat_id), reply_markup=keyboard.build().as_markup())
        db.add_account(chat_id,username)
        
        
    await message.answer("Welcome to a validator monitoring bot by P2P.org\n\n\n\n",reply_markup=menu.as_markup())
