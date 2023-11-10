from __main__ import router,dp,db,bot,admin_chat,cb
from utils.menu_builder import MenuBuilder
from aiogram.types import Message
from aiogram import F

@router.message(F.content_type.in_({'text', 'sticker','photo'}))
async def command_start(message: Message) -> None:
    if str(message.chat.id).startswith('-'):
        await message.answer("🧑🤝🧑 Group chats are not allowed.\nSorry and have a good day.")
        return

    username = message.chat.username
    chat_id = message.from_user.id
    account_status = db.get_records('account_status','id',chat_id)
    
    menu = MenuBuilder()
    menu = menu.build(callback_data=cb,preset='main_menu')

    if account_status and account_status == 'off':
        await message.answer(chat_id,"Your account has been disabled 🤷\nSorry and have a good day.")
        return

    if not account_status:
        await bot.send_message(admin_chat, "Username: @{} ID: {}\nHas just PRE-registered.".format(username,chat_id))
        db.add_account(chat_id,username)
        
        await message.answer("Hi there 👋\n\n\nWelcome to a validator monitoring bot by P2P.org\n\n\n\n",reply_markup=menu.as_markup())
    else:
        await message.answer("Here is main menu",reply_markup=menu.as_markup())
